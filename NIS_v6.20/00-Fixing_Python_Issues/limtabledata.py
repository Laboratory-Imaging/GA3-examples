from __future__ import annotations

import copy, json, re
import numpy as np

from html import escape as html_escape

import matplotlib.pyplot as mpl
import matplotlib.colors as mplcolors

from typing import Callable, Sequence, TypeAlias

ColSpecifier: TypeAlias = int|str
MultiColSpecifier: TypeAlias = int|str|slice|Callable[[int,str,dict],bool]|Sequence[int|str]
CellData: TypeAlias = int|float|str|None
ColData: TypeAlias = Sequence[int|float|str|None]|np.ndarray
MultiColData: TypeAlias = ColData|Sequence[ColData]|np.ndarray

def _is_cols_scalar(cols) -> bool:
    return type(cols) == int or type(cols) == str

def _decltype_to_python(decltype: str):
    if decltype == 'int':
        return int
    if decltype == 'double':
        return float
    return str

class LimTableDataBase:

    def __init__(
        self,
        *args: LimTableDataBase,
        tabName: str|None = None,
        tabMetadata: dict|None = None,
        privateTables: dict|None = None
        ):

        if 0 == len(args):
            self.__tabName_ = tabName if type(tabName) == str else ""
            self.__tabMeta_ = tabMetadata if type(tabMetadata) == dict else {}
            self.__privateTables_ = privateTables if type(privateTables) == dict else {}
            self.__colIds_, self.__colMeta_, self.__colData_ = [], [], []

        elif 1 == len(args) and isinstance(args[0], LimTableDataBase):
            source, memo = args[0], {}
            self.__tabName_ = tabName if type(tabName) == str else source.__tabName_
            self.__tabMeta_ = tabMetadata if type(tabMetadata) == dict else copy.deepcopy(source.__tabMeta_, memo)
            self.__privateTables_ = privateTables if type(privateTables) == dict else copy.deepcopy(source.__privateTables_, memo)
            self.__colIds_ = copy.deepcopy(source.__colIds_, memo)
            self.__colMeta_ = copy.deepcopy(source.__colMeta_, memo)
            self.__colData_ = copy.deepcopy(source.__colData_, memo)

        elif 1 <= len(args) and type(args[0]) == tuple and 2 <= len(args[0]):
            self.__tabName_ = tabName if type(tabName) == str else ""
            self.__tabMeta_ = tabMetadata if type(tabMetadata) == dict else {}
            self.__privateTables_ = privateTables if type(privateTables) == dict else {}
            self.__colIds_, self.__colMeta_, self.__colData_ = [], [], []
            for index, source in enumerate(args):
                if type(source) == tuple and 2 < len(source):
                    self.insertCol(*source)
                else:
                    raise TypeError(f'Type of argument args[{index}] not a column tuple')
        else:
            raise TypeError(f'Type of argument source must be PySharedTable or LimTableData')

    @classmethod
    def cppInit(self, coldefs, name, meta, pTables):
        if type(meta) == str :
            meta = json.loads(meta)
        checked_coldefs = []
        for colname, coldata, colmeta in coldefs:
            if type(colmeta) == str:
                colmeta = json.loads(colmeta)
            checked_coldefs.append((colname, coldata, colmeta))
        return self(*checked_coldefs, tabName=name, tabMetadata=meta, privateTables=pTables)

    @property
    def tableName(self) -> str:
        """Table name."""
        return self.__tabName_

    def setTableName(self, name : str):
        self.__tabName_ = name

    @property
    def tableMetadata(self) -> dict:
        """Table metadata as a dict."""
        return self.__tabMeta_

    @property
    def tableMetadataAsJson(self) -> str:
        """Table metadata as json string."""
        return json.dumps(self.__tabMeta_)

    def setTableMetadata(self, meta : dict):
        self.__tabMeta_ = meta

    @property
    def colIdList(self) -> list[str]:
        """All column ids as a list."""
        return self.__colIds_

    @property
    def colTitleList(self) -> list[str]:
        """All column titles as a list."""
        return [m.get("title", "") for m in self.__colMeta_]

    @property
    def colMetadataList(self) -> list[dict]:
        """All column metadata as a list."""
        return self.__colMeta_

    @property
    def colMetadataListAsJson(self) -> list[str]:
        """All column metadata list as json string."""
        return json.dumps(self.__colMeta_)

    @property
    def colCount(self) -> int:
        """Number of columns."""
        return len(self.__colIds_)

    @property
    def rowCount(self) -> int:
        """Number of rows."""
        return max((len(data) for data in self.__colData_), default=0)

    @property
    def colDataList(self) -> list[list]:
        """All data (column major) as list of lists."""
        return self.__colData_

    @property
    def rowDataList(self) -> list[list]:
        """All data (row major) as list of lists."""
        return list(zip(*self.colDataList))

    @property
    def groupedBy(self) -> list[int]:
        """Column indexes used for grouping as a list."""
        return [ i for i in [ self.colIndexById(id) for id in self.__tabMeta_.get("groupedBy", []) ] if 0 <= i ]

    @property
    def groups(self) -> list[list[int]]:
        """Grouped row indexes as a list of lists.

        Rows are assingned to groups according to the value of the groupedBy columns.

        Returns:
            list of groups each containing a list of row indexes.
        """
        rows = self.rowData(self.groupedBy)
        if not rows:
            return [ list(range(self.rowCount)) ]
        g, lst = 0, [ [ 0 ] ]
        for i in range(1, len(rows)):
            if rows[i] == rows[i - 1]:
                lst[g].append(i)
            else:
                g += 1
                lst.append([ i, ])
        return lst

    @property
    def privateTables(self) -> dict[str,LimTableDataBase]:
        """Private tables as a dictionary."""
        return self.__privateTables_

    @property
    def tableSystemFlags(self) -> list[str]:
        """System flags of the table as a list."""
        return self.__tabMeta_.get('_systemFlags', [])

    @property
    def isWebpage(self) -> bool:
        """Webpage flag test."""
        return "webpage" in self.tableSystemFlags

    @property
    def webpageControls(self) -> list:
        """Controls in the webpage as a list."""
        if not self.isWebpage:
            return []
        cols = self.colIndexList(lambda i, id, m: m.get('feature', None) == 'jsonInitialState')
        if not cols:
            return []
        initialState = json.loads(self.cellData(cols[0], 0))
        panes = initialState["panes"]
        controls = []
        for p in panes:
            for t in p["state"]["tabs"]:
                try:
                    state = t["state"]
                    table = self.privateTables[state["_tableName"]]
                    controls.append((t["className"], table, state))
                except:
                    pass
        return controls

    def content(self):
        """Returns JSON string describing inner content (panes and items)"""
        if not self.isWebpage:
            return "{ }"
        content = {}
        cols = self.colIndexList(lambda i, id, m: m.get('feature', None) == 'jsonInitialState')
        if not cols:
            return None
        initialState = json.loads(self.cellData(cols[0], 0))
        panes = initialState["panes"]
        output = []
        for p in panes:
            items = []
            for t in p["state"]["tabs"]:
                items.append(t["className"])
            output.append({'items': items})
        return json.dumps({'panes': output}, indent=4)

    def pane(self, index):
        """Extracts single pane by index"""
        if not self.isWebpage:
            return None
        cols = self.colIndexList(lambda i, id, m: m.get('feature', None) == 'jsonInitialState')
        if not cols:
            return None
        initialState = json.loads(self.cellData(cols[0], 0))
        panes = initialState["panes"]
        if index < 0 or index >= len(panes):
            return None
        newState = { "panes": [panes[index]] }
        tables = []
        for t in newState["panes"][0]["state"]["tabs"]:
            try:
                tables.append(t["state"]["_tableName"])
            except:
                pass

        deep_copy = copy.deepcopy(self)
        deep_copy.__colData_[cols[0]][0] = json.dumps(newState)
        for k in list(deep_copy.__privateTables_.keys()):
            if k not in tables:
                del deep_copy.__privateTables_[k]
        return deep_copy

    def item(self, index):
        """Extracts single graph by index"""
        if not self.isWebpage:
            return None
        cols = self.colIndexList(lambda i, id, m: m.get('feature', None) == 'jsonInitialState')
        if not cols:
            return None
        initialState = json.loads(self.cellData(cols[0], 0))
        panes = initialState["panes"]

        tables = []
        tabIndex = 0
        newState = None
        for p in panes:
            for t in p["state"]["tabs"]:
                if tabIndex == index:
                    newPane = copy.deepcopy(p)
                    newPane["state"]["tabs"] = [t]
                    newState = { "panes": [newPane] }
                    tables.append(t["state"]["_tableName"])
                tabIndex += 1
        if newState:
            deep_copy = copy.deepcopy(self)
            deep_copy.__colData_[cols[0]][0] = json.dumps(newState)
            for k in list(deep_copy.__privateTables_.keys()):
                if k not in tables:
                    del deep_copy.__privateTables_[k]
            return deep_copy
        return None

    def slice(self, *args):
        """Return slice to be used for indexing.

        Can be called with slice(b) or slice(a[, b[, c]])

        Args:
            a (int): start index
            b (int): end index
            c (int): step

        Returns:
            a slice object
        """
        a, b, c, n = None, None, None, len(args)
        if n <= 0:
            raise ValueError('At least one argument required (start=None, stop, step=None)')
        if 1 <= n:
            a = self.colCount if args[0] == 'N' else (args[0] if type(args[0]) == int else self.colIndexList(args[0])[0])
        if 2 <= n:
            b = self.colCount if args[1] == 'N' else (args[1] if type(args[1]) == int else self.colIndexList(args[1])[0])
        if 3 <= n:
            c = args[2] if type(args[2]) == int else self.colIndexList(args[2])[0]
        return slice(a) if 1 == n else slice(a, b, c)

    def colIndexById(self, colId: str) -> int:
        """Return column index if column with given id exists or -1."""
        try:
            return self.__colIds_.index(colId)
        except ValueError:
            return -1

    def colIndexByPattern(self, pattern: str) -> int:
        """Return column index if given pattern matches title or id or -1 if there is no such column.

        Note that re.search() is used. In order to match full title use "^pattern$". Case-insensitive
        matching is used. Id is compared for equality.

        Args:
            pattern: a regexp pattern

        Returns:
            The index of first match or -1 in case there is no match.
        """
        if type(pattern) == str and pattern != "":
            regexp = re.compile(pattern, re.I)
            for index, colId in enumerate(self.__colIds_):
                if pattern == colId or regexp.search(self.__colMeta_[index].get('title', '')):
                    return index
        return -1

    def colIndexListByPattern(self, pattern: str) -> list[int]:
        retList = []
        if type(pattern) == str and pattern != "":
            regexp = re.compile(pattern, re.I)
            for index, colId in enumerate(self.__colIds_):
                if pattern == colId or regexp.search(self.__colMeta_[index].get('title', '')):
                    retList.append(index)
        return retList

    def hasColumn(self, col: ColSpecifier|Callable) -> bool:
        """Return True if a column is in the table."""
        return 0 <= self.colIndex(col, check=False)

    def colIndex(self, col: ColSpecifier|Callable, *, check: bool = True) -> int:
        """Return column index of given column.

        Args:
            col: column specifier
            check: if column is not present raise an exception

        Returns:
            Index of the column or -1 if not found.

        Raises:
            ValueError: if check is True and object is not present
            IndexError: if check is True and object is not present
        """
        if type(col) == int:
            if check and not (0 <= col and col < self.colCount):
                raise IndexError(f'Argument col - index ({col}) out of range')
            elif 0 <= col and col < self.colCount:
                return col
            else:
                return -1
        elif type(col) == str:
            index = self.colIndexByPattern(col)
            if check and index < 0:
                raise ValueError(f'Argument col - value ({col}) did not match')
            else:
                return index
        elif callable(col):
            for index, idmeta in enumerate(zip(self.__colIds_, self.__colMeta_)):
                if col(index, *idmeta):
                    return index
            if check:
                raise ValueError(f'Argument col() - did not match')
            else:
                return -1
        elif check:
            raise TypeError('Type of argument col not supported')
        else:
            return -1

    def colIndexList(self, cols: MultiColSpecifier|None = None, *, check: bool = True) -> list[int]:
        """Return list of column indexes satisfying the column specifier.

        Args:
            cols: column specifier
            check: if column is not present raise an exception

        Returns:
            list of columns indexes.

        Raises:
            ValueError: if check is True and object is not present
            IndexError: if check is True and object is not present
        """
        if cols is None:
            return list(range(self.colCount))
        elif type(cols) == int:
            if not check or (0 <= cols and cols < self.colCount):
                return [ cols ]
            else:
                raise IndexError(f'Argument cols - index ({cols}) out of range')
        elif type(cols) == str:
            index = self.colIndex(cols, check=check)
            if check and index < 0:
                raise ValueError(f'Argument cols - value ({cols}) did not match')
            else:
                return [ index ]
        elif type(cols) == slice:
            return list(range(*cols.indices(self.colCount)))
        elif callable(cols):
            return [ index for index, idmeta in enumerate(zip(self.__colIds_, self.__colMeta_)) if cols(index, *idmeta) ]
        elif type(cols) == list or type(cols) == tuple:
            indexes = []
            for i, item in enumerate(cols):
                if type(item) == int:
                    if not check or (0 <= item and item < self.colCount):
                        indexes.append(item)
                    else:
                        raise IndexError(f'Argument cols[{i}] - index ({item}) out of range')
                elif type(item) == str:
                    index = self.colIndex(item, check=check)
                    if check and index < 0:
                        raise ValueError(f'Argument cols[{i}] - value ({item}) did not match')
                    else:
                        indexes.append(index)
                elif check:
                    raise TypeError(f'Type of argument cols[{i}] not supported')
                else:
                    indexes.append(-1)
            return indexes
        elif check:
            raise TypeError('Type of argument cols not supported')

    def __col_getter_(self, fn: Callable[[int], any], cols: MultiColSpecifier|None = None) -> any:
        indexes = self.colIndexList(cols)
        ret = [ fn(i) for i in indexes]
        return ret[0] if _is_cols_scalar(cols) else ret

    def colId(self, cols: MultiColSpecifier|None = None):
        """Return column id or list of ids of given cols."""
        if type(cols) is int:
            return self.colIdList[cols] if 0 <= cols and cols < len(self.colIdList) else None
        if type(cols) is list:
            return [(self.colIdList[col] if type(col) is int and 0 <= col and col < len(self.colIdList) else None) for col in cols]
        return None

    def __colPythonType_(self, index : int):
        return _decltype_to_python(self.__colMeta_[index].get("decltype", ""))

    def colTitle(self, cols: MultiColSpecifier|None = None):
        return self.__col_getter_(lambda i: self.__colMeta_[i].get('title', ''), cols)

    def colTitleAndUnit(self, cols: MultiColSpecifier|None = None):
        def titleAndUnitAt(i):
            m = self.__colMeta_[i]
            return f"{m['title']} [{m['units']}]" if 'units' in m and type(m['units']) == str and 0 < len(m['units']) else m['title']
        return self.__col_getter_(titleAndUnitAt, cols)

    def colDeclType(self, cols: MultiColSpecifier|None = None):
        return self.__col_getter_(lambda i: self.__colPythonType_(i), cols)


    def colIsVisible(self,
        cols: MultiColSpecifier|None = None,
        *,
        override: MultiColSpecifier|None = None,
        forceShow: MultiColSpecifier|None = None,
        forceHide: MultiColSpecifier|None = None) -> bool|list[bool]:

        indexes = self.colIndexListByPattern(override) if type(override) == str else (self.colIndexList(override) if override is not None else None)
        showIndexes = self.colIndexListByPattern(forceShow) if type(forceShow) == str else (self.colIndexList(forceShow) if forceShow is not None else None)
        hideIndexes = self.colIndexListByPattern(forceHide) if type(forceHide) == str else (self.colIndexList(forceHide) if forceHide is not None else None)
        def isVisibleAt(i):
            if not (indexes is None):
                return i in indexes
            if showIndexes and i in showIndexes:
                return True
            if hideIndexes and i in hideIndexes:
                return False
            return not self.__colMeta_[i].get('hidden', False)
        return self.__col_getter_(isVisibleAt, cols)

    def colIsNumeric(self, cols: MultiColSpecifier|None = None):
        def isNumericAt(i):
            dt = self.__colPythonType_(i)
            return dt == int or dt == float
        return self.__col_getter_(isNumericAt, cols)

    def colIsJsonObject(self, cols: MultiColSpecifier|None = None):
        def isJsonOjectAt(i):
            return self.__colMeta_[i].get('jsonObject', None)
        return self.__col_getter_(isJsonOjectAt, cols)

    def colMetadata(self, cols: MultiColSpecifier|None = None, keys: str|list[str] = None):
        if keys is None:
            return self.__col_getter_(lambda i: self.__colMeta_[i], cols)
        elif type(keys) == str:
            return self.__col_getter_(lambda i: self.__colMeta_[i].get(keys, None), cols)
        elif type(keys) == list:
            return self.__col_getter_(lambda i: [self.__colMeta_[i].get(k, None) for k in keys], cols)
        else:
            raise TypeError('Type of argument keys must be str, list or None')

    def colData(self, cols: MultiColSpecifier|None = None) -> list[CellData]|list[list[CellData]]:
        return self.__col_getter_(lambda i: self.__colData_[i], cols)

    def clearColData(self, cols: MultiColSpecifier|None = None) -> None:
        index = self.colIndexList(cols)
        for i in range(len(index)):
            self.__colData_[index[i]].clear()

    def setColData(self, cols: MultiColSpecifier, data: MultiColData) -> None:
        index = self.colIndexList(cols)
        if _is_cols_scalar(cols) and len(index) == 1:
            index = index[0]
        if type(index) == int:
            if isinstance(data, Sequence):
                self.__colData_[index] = list(data)
            elif isinstance(data, np.ndarray) and 1 == data.ndim:
                self.__colData_[index] = data.tolist() if isinstance(data, np.ma.masked_array) else np.ma.masked_invalid(data).tolist()
            else:
                raise ValueError('Argument data must be either a Sequence or a 1D numpy array.')
        elif isinstance(index, Sequence):
            if  isinstance(data, Sequence) and all(isinstance(item, Sequence) for item in data):
                for i, d in zip(index, data):
                    self.__colData_[i] = list(d)
            elif isinstance(data, Sequence) and all(isinstance(item, np.ndarray) and 1 == item.ndim for item in data):
                for i, d in zip(index, data):
                    self.__colData_[i] = d.tolist() if isinstance(d, np.ma.masked_array) else np.ma.masked_invalid(d).tolist()
            elif isinstance(data, np.ndarray) and 2 == data.ndim and len(index) == data.shape[0]:
                for i in range(len(index)):
                    d = data[i]
                    self.__colData_[index[i]] = d.tolist() if isinstance(d, np.ma.masked_array) else np.ma.masked_invalid(d).tolist()
            else:
                raise ValueError('Argument data must be either a Sequence of Sequences or a 1D or 2D numpy array.')

    def appendColData(self, cols: MultiColSpecifier, data: MultiColData) -> None:
        index = self.colIndexList(cols)
        if _is_cols_scalar(cols) and len(index) == 1:
            index = index[0]
        if type(index) == int:
            self.__colData_[index].append(data)
        elif type(index) == list:
            for i in range(len(index)):
                self.__colData_[index[i]].append(data[i])
        else:
            raise ValueError('Argument data must be list of lists if cols is a list or list of data if cols is a scalar.')

    def colJsonObjectDisplay(self, cols: MultiColSpecifier|None = None):
        return self.__col_getter_(lambda i: json.loads(self.__colData_[i]).get('disp', None), cols)

    def colNanArray(self, cols: MultiColSpecifier|None = None) -> np.ndarray:
        def arrayAt(i):
            dt = self.__colPythonType_(i)
            data = self.__colData_[i]
            if dt == int or dt == float:
                nan = float('nan')
                return np.array([x if x is not None else nan for x in data])
            else:
                return np.array([x or "" for x in data])
        return self.__col_getter_(arrayAt, cols)

    def colArray(self, cols: MultiColSpecifier|None = None) -> np.ndarray:
        def maskedArrayAt(i):
            dt = self.__colPythonType_(i)
            data = self.__colData_[i]
            mask = [x is None for x in data]
            if dt == int:
                return np.ma.masked_array([0 if x is None else x for x in data], mask=mask)
            elif dt == float:
                nan = float('nan')
                return np.ma.masked_array([nan if x is None else x for x in data], mask=mask)
            else:
                return np.ma.masked_array(["" if x is None else x for x in data], mask=mask)
        return self.__col_getter_(maskedArrayAt, cols)

    def rowData(self, cols: MultiColSpecifier|None = None):
        return list(zip(*self.colData(cols)))

    def cellData(self, colIndex, rowIndex):
        return self.__colData_[colIndex][rowIndex]

    def colDataStats(self, statistics:Callable|str|Sequence[Callable|str], cols: MultiColSpecifier|None = None):
        def stat(a, stat):
            statfunc = {
                'min': np.min,
                'max': np.max,
                'mean': np.mean,
                'stdev': np.std,
                'sum': np.sum
            }
            if stat in statfunc:
                try:
                    return statfunc[stat](a).tolist()
                except:
                    return None
            elif callable(stat):
                try:
                    return stat(a).tolist()
                except:
                    return None
            return None

        if type(statistics) == str or callable(statistics):
            return self.__col_getter_(lambda i: stat(self.colArray(i), statistics), cols)
        elif type(statistics) == list or type(statistics) == tuple:
            return self.__col_getter_(lambda i: [ stat(self.colArray(i), s) for s in statistics ], cols)
        else:
            raise TypeError('Type of argument statistics must be string, Callable or list of those')

    def min(self, cols: MultiColSpecifier|None = None) -> float:
        return self.colDataStats('min', cols)

    def max(self, cols: MultiColSpecifier|None = None) -> float:
        return self.colDataStats('max', cols)

    def minMax(self, cols: MultiColSpecifier|None = None) -> float:
        return self.colDataStats(['min', 'max'], cols)

    def mean(self, cols: MultiColSpecifier|None = None) -> float:
        return self.colDataStats('mean', cols)

    def groupNames(self, separator=None):
        gnames = []
        if separator is None:
            separator = ", "
        gcolumns = self.groupedBy
        if 0 < len(gcolumns):
            for i, grows in enumerate(self.groups):
                groupData = [self.cellData(col, grows[0]) for col in gcolumns]
                groupData = filter(lambda x: x is not None, groupData)
                groupData = [str(x) for x in groupData]
                gnames.append(separator.join(groupData))
        return gnames

    def colColorMap(self, col: int|str, cmap: str|mplcolors.Colormap, norm: str|mplcolors.Normalize|None = None, *, alpha:float|None = None, vmin:float|None = None, vmax:float|None = None, vlist: list[str]|None = None):
        if not (type(col) == int or type(col) == str):
            raise TypeError('Type of argument col must be str or int')
        index = self.colIndexList(col)[0]
        dt = self.__colPythonType_(index)
        if dt == int or dt == float:
            if type(cmap) == str:
                cmap = mpl.get_cmap(cmap)
            if not isinstance(cmap, mplcolors.Colormap):
                raise TypeError('Type of argument cmap must be string or an instance of mplcolors.Colormap')
            if norm is None:
                norm = mplcolors.Normalize(vmin, vmax)
            if norm  == 'log':
                norm = mplcolors.LogNorm(vmin, vmax)
            if not isinstance(norm, mplcolors.Normalize):
                raise TypeError('Type of argument norm must be an instance of mplcolors.Normalize')
            return [ mplcolors.to_hex(tuple(item), True) for item in cmap(norm(self.colMaskedArray(index)), alpha).tolist() ]

        else:
            data = self.__colData_[index]
            if vlist is None:
                vlist = list(set(data))
            if type(cmap) == str:
                cmap = mpl.get_cmap(cmap, len(vlist))
            if not isinstance(cmap, mplcolors.Colormap):
                raise TypeError('Type of argument cmap must be string or an instance of mplcolors.Colormap')
            vlist.sort()
            cols = [ mplcolors.to_hex(tuple(item), True) for item in cmap(np.arange(len(vlist)), alpha).tolist() ]
            colmap = { k: v for k, v in zip(vlist, cols) }
            return [ colmap.get(item, cmap.get_bad()) for item in data ]

    def __fix_col_len(self):
        rowCount = self.rowCount
        for col in self.__colData_:
            n = len(col)
            if n < rowCount:
                col += [ None, ] * (rowCount - n)

    def __make_col_tuple(self, id: str, data: list, meta: dict|None = None) -> tuple[str, list, dict|None]:
        def guessDeclType(lst):
            valid = [x for x in lst if x is not None]
            if len(valid) == 0:
                raise ValueError('Argument data must not be empty if meta["decltype"] not provided')
            if type(valid[0]) == int:
                return 'int'
            elif type(valid[0]) == float:
                return 'double'
            elif type(valid[0]) == str:
                return 'QString'
            else:
                raise TypeError('At lease one item in argument data[i] must be int, float or str if meta["decltype"] not provided')

        if type(id) != str:
            raise TypeError('Type of argument id must be string')
        if id in self.__colIds_:
            raise ValueError(f'Argument id={id} already used')

        if type(data) == tuple:
            data = list(data)
        elif type(data) != list:
            raise TypeError('Type of argument data must be list')

        if meta is None:
            meta = { 'title': id, 'decltype': guessDeclType(data) }
        if type(meta) != dict:
            raise TypeError('Type of argument meta must be dict')
        if 'decltype' not in meta:
            meta['decltype'] = guessDeclType(data)
        if meta['decltype'] not in ( 'int', 'double', 'QString' ):
            raise ValueError(f'Argument meta["decltype"] contains invalid type "{meta["decltype"]}" not in ("int", "double", "QString")')
        if 'title' not in meta:
            meta['title'] = id

        return (id, data, meta)

    def insertPrivateTable(self, table : LimTableDataBase) -> None:
        self.__privateTables_[table.tableName] = table

    def insertCol(self, id: str, data: list, meta: dict|None = None, *, before: int|str|None = None, after: int|str|None = None) -> None:
        col = self.__make_col_tuple(id, data, meta)
        at = self.colCount
        if type(before) == int or type(before) == str:
            at = self.colIndex(before)[0]
        elif type(after) == int or type(after) == str:
            at = self.colIndex(after)[0] + 1
        self.__colIds_.insert(at, col[0])
        self.__colData_.insert(at, col[1])
        self.__colMeta_.insert(at, col[2])
        self.__fix_col_len()

    def removeCol(self, at: ColSpecifier|None = None) -> None:
        index = self.colCount-1 if at is None else self.colIndex(at)
        del self.__colIds_[index]
        del self.__colData_[index]
        del self.__colMeta_[index]

    def removeAllCols(self) -> None:
        self.__colIds_.clear()
        self.__colData_.clear()
        self.__colMeta_.clear()

    def __select_cols(self, *columns: int|str|slice|tuple[str,list,dict|None]) -> None:
        colIds, colData, colMeta = [], [], []
        for icol, column in enumerate(columns):
            if column == '*':
                for index in range(self.colCount):
                    colIds.append(self.__colIds_[index])
                    colData.append(self.__colData_[index])
                    colMeta.append(self.__colMeta_[index])
            elif type(column) == slice:
                for index in range(*column.indices(self.colCount)):
                    colIds.append(self.__colIds_[index])
                    colData.append(self.__colData_[index])
                    colMeta.append(self.__colMeta_[index])
            elif type(column) == int or type(column) == str:
                index = self.colIndexList(column)[0]
                colIds.append(self.__colIds_[index])
                colData.append(self.__colData_[index])
                colMeta.append(self.__colMeta_[index])
            elif type(column) == tuple:
                col = self.__make_col_tuple(*column)
                colIds.append(col[0])
                colData.append(col[1])
                colMeta.append(col[2])
            else:
                raise TypeError(f'Type of argument at {icol} must be int, str or tuple[str, list, dict|None] but is {type(column)}')
        return zip(colIds, colData, colMeta)

    def select(self, *columns: int|str|slice|tuple[str,list,dict|None]) -> None:
        coldefs = self.__select_cols(*columns)
        self.__colIds_, self.__colData_, self.__colMeta_ = zip(*coldefs)

    def selected(self, *columns: int|str|slice|tuple[str,list,dict|None], filter_ : list[int]|list[bool]|None = None, onError: LimTableDataBase|None = None) -> LimTableDataBase:
        try:
            coldefs = self.__select_cols(*columns)
            if filter_ is not None:
                filteredColdefs = []
                n = self.rowCount
                indexes = self.__filter_(filter_)
                for coldef in coldefs:
                    data = coldef[1]
                    colData = [ data[i] for i in indexes if 0 <= i and i < n ]
                    filteredColdefs.append((coldef[0], colData, coldef[2]))
                coldefs = filteredColdefs
            return LimTableDataBase(*coldefs, tabName=self.tableName, tabMetadata=self.tableMetadata, privateTables=self.privateTables)
        except:
            if type(onError) == str and onError.lower() == 'empty':
                return LimTableDataBase()
            elif isinstance(onError, LimTableDataBase):
                return onError
            elif onError is not None:
                return TypeError('Type of argument onError must be str=="empty" or LimTableDataBase')
            else:
                raise

    def __filter_(self,
            flt: Callable[..., bool]|list[int]|list[bool],
            cols: MultiColSpecifier = None,
            *args) -> list[int]:
        n = self.rowCount
        if callable(flt):
            indexes = self.colIndexList(cols)
            return [ index for index, row in enumerate(self.rowData(indexes)) if flt(*row, *args) ]
        elif type(flt) == list and len(flt) and type(flt[0]) == int:
            return flt
        elif type(flt) == list and len(flt) == n and type(flt[0]) == bool:
            return [ index for index, val in enumerate(flt) if val ]
        else:
            raise TypeError('Type of argument flt must be Callable or list')

    def filter(self,
            flt: Callable[..., bool]|list[int]|list[bool],
            cols: MultiColSpecifier = None,
            *args) -> None:
        n = self.rowCount
        indexes = self.__filter_(flt, cols, *args)
        self.__colData_ = [ [ col[i] for i in indexes if 0 <= i and i < n ] for col in self.__colData_ ]

    def filtered(self,
            flt: Callable[..., bool]|list[int]|list[bool],
            cols: MultiColSpecifier = None,
            *args,
            onError: LimTableDataBase|None = None) -> LimTableDataBase:
        try:
            n = self.rowCount
            indexes = self.__filter_(flt, cols, *args)
            coldefs = zip(self.colIdList, [ [ col[i] for i in indexes if 0 <= i and i < n ] for col in self.__colData_ ], self.colMetadataList)
            return LimTableDataBase(*coldefs, tabName=self.tableName, tabMetadata=self.tableMetadata, privateTables=self.privateTables)
        except:
            if type(onError) == str and onError.lower() == 'empty':
                return LimTableDataBase()
            elif isinstance(onError, LimTableDataBase):
                return onError
            elif onError is not None:
                return TypeError('Type of argument onError must be str=="empty" or LimTableDataBase')
            else:
                raise

    def evalFilter(self,
            flt: Callable[..., bool],
            cols: MultiColSpecifier = None,
            *args) -> list[bool]:
        if not callable(flt):
            raise TypeError('Type of argument flt is not callable')
        indexes = [ i for i in self.colIndexList(cols, check=False) if 0 <= i ]
        if 0 == len(indexes):
            return [False, ] * self.rowCount
        if 1 == len(indexes):
            return [ flt(val, *args) for val in self.colDataList[indexes[0]] ]
        else:
            return [ flt(*row, *args) for row in self.rowData(indexes) ]

    def sort(self, *cols: MultiColSpecifier, ascending: bool = True, first: int = None, last: int = None) -> None:
        indexes = self.colIndexList(cols)
        if len(indexes):
            order = list(range(self.rowCount))
            while len(indexes):
                index = indexes[-1]
                data = self.__colData_[index]
                decorated = [ (data[i], i) for i in order ]
                decorated.sort()
                indexes.pop()
                order = [ item[1] for item in decorated ]
            if not ascending:
                order.reverse()
            self.__colData_ = [[ col[i] for i in order ] for col in self.__colData_]
        fdata, ldata = [], []
        if type(first) == int:
            fdata = [[ col[i] for i in range(first) ] for col in self.__colData_]
        if type(last) == int:
            s = slice(-last, self.rowCount)
            ldata = [[ col[i] for i in range(*s.indices(len(col))) ] for col in self.__colData_]
        if len(fdata) and len(ldata):
            self.__colData_ = [ f + l for f, l in zip(fdata, ldata) ]
        elif len(fdata):
            self.__colData_ = fdata
        elif len(ldata):
            self.__colData_ = ldata

    def sorted(self, *cols: MultiColSpecifier, ascending: bool = True, first: int = None, last: int = None, onError: LimTableDataBase|None = None) -> LimTableDataBase:
        try:
            ret = LimTableDataBase(self)
            ret.sort(*cols, ascending=ascending, first=first, last=last)
            return ret
        except:
            if type(onError) == str and onError.lower() == 'empty':
                return LimTableDataBase()
            elif isinstance(onError, LimTableDataBase):
                return onError
            elif onError is not None:
                return TypeError('Type of argument onError must be str=="empty" or LimTableDataBase')
            else:
                raise
