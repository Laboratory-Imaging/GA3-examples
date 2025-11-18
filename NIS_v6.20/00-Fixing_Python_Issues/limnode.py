from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, TypeAlias

import enum, subprocess, os

try:
    import numpy as np
    NumpyArray: TypeAlias = np.ndarray
except ImportError:
    NumpyArray: TypeAlias = Any

try:
    from numpy.lib.stride_tricks import as_strided
except ImportError:
    pass

try:
    from limtabledata import LimTableDataBase, MultiColSpecifier, MultiColData
except ImportError:
    LimTableDataBase: TypeAlias = Any
    MultiColSpecifier: TypeAlias = Any
    MultiColData: TypeAlias = Any

AnyColorDef: TypeAlias = int|str|tuple[int, int, int]

@dataclass(frozen=True, kw_only=True)
class Node:
    name: str
    uuid: str
    defaultName: str

class ExperimentLoopType(enum.IntEnum):
    loopTypeUnknown  = 0
    loopTypePlate    = 1
    loopTypeWell     = 2
    loopTypeXYSite   = 3
    loopTypeTLapse   = 4
    loopTypeZStack   = 5
    loopTypeCount    = 6
    loopTypeSlide    = 7
    loopTypeRegion   = 8
    loopTypeTemporary= 9

@dataclass(frozen=True, kw_only=True)
class LoopDef:
    name: str
    type: ExperimentLoopType
    index: int

    def __post_init__(self):
        if type(self.type) == int:
            object.__setattr__(self, 'type', ExperimentLoopType(self.type))

@dataclass(frozen=True, kw_only=True)
class ParameterDef:
    parentNode: Node
    parName: str
    parIsInput: bool
    loopDefList: list[LoopDef]

    def __post_init__(self):
        if type(self.parentNode) == dict:
            object.__setattr__(self, 'parentNode', Node(**self.parentNode))
        if type(self.loopDefList) == list and all(type(item) == dict for item in self.loopDefList):
            object.__setattr__(self, 'loopDefList', [LoopDef(**item) for item in self.loopDefList])

@dataclass(frozen=True, kw_only=True)
class Metadata:
    componentCount: int
    bitsPerComponent: int
    size: tuple[int, int, int]
    calibration: tuple[float, float, float]
    alignment: int

    @property
    def calibrated(self) -> tuple[bool, bool, bool]:
        return (0 < self.calibration[0], 0 < self.calibration[1], 0 < self.calibration[2])
    @property
    def units(self) -> tuple[str, str, str]:
        return tuple("\xB5m" if cal else "px" for cal in self.calibrated)

    def withDifferentSize(self, size: tuple[int, int, int], calibration: tuple[float, float, float]|None = None) -> Metadata:
        if size is not None:
            if type(size) == tuple and len(size) == 3:
                object.__setattr__(self, 'size', size)
                if calibration is not None:
                    if type(calibration) == tuple and len(calibration) == 3:
                        object.__setattr__(self, 'calibration', calibration)
                    else:
                        raise TypeError("Expected calibration: tuple[int, int, int]")
            else:
                raise TypeError("Expected size: tuple[int, int, int]")
        return self

    def copyMetadataFrom(self, other: Metadata) -> Metadata:
        object.__setattr__(self, 'componentCount', other.componentCount)
        object.__setattr__(self, 'bitsPerComponent', other.bitsPerComponent)
        object.__setattr__(self, 'size', other.size)
        object.__setattr__(self, 'calibration', other.calibration)
        object.__setattr__(self, 'alignment', other.alignment)
        return self

@dataclass(frozen=True, kw_only=True)
class InputChannelDef(ParameterDef, Metadata):
    channelName: str
    channelColor: int

@dataclass(frozen=True, kw_only=True)
class OutputChannelDef(ParameterDef, Metadata):
    assignedParName: str|None = None
    channelName: str|None = None
    channelColor: int|None = None

    def assign(self, param: InputChannelDef) -> OutputChannelDef:
        if isinstance(param, InputChannelDef):
            object.__setattr__(self, 'assignedParName', param.parName)
            object.__setattr__(self, 'channelName', param.channelName)
            object.__setattr__(self, 'channelColor', param.channelColor)
        else:
            raise TypeError('Expected param: str|InputChannelDef')
        return self

    def makeNewMono(self, name: str, color: AnyColorDef) -> OutputChannelDef:
        object.__setattr__(self, 'assignedParName', None)
        object.__setattr__(self, 'channelName', name)
        object.__setattr__(self, 'channelColor', _parse_color(color))
        object.__setattr__(self, 'componentCount', 1)
        return self

    def makeNewRgb(self, name: str|None = None) -> OutputChannelDef:
        object.__setattr__(self, 'assignedParName', None)
        object.__setattr__(self, 'channelName', name)
        object.__setattr__(self, 'channelColor', None)
        object.__setattr__(self, 'componentCount', 3)
        return self

    def makeFloat(self) -> OutputChannelDef:
        object.__setattr__(self, 'bitsPerComponent', 32)
        return self

    def makeUInt16(self) -> OutputChannelDef:
        object.__setattr__(self, 'bitsPerComponent', 16)
        return self

    def makeUInt8(self) -> OutputChannelDef:
        object.__setattr__(self, 'bitsPerComponent', 8)
        return self

    def copyFrom(self, other: OutputChannelDef) -> OutputChannelDef:
        object.__setattr__(self, 'assignedParName', other.assignedParName)
        object.__setattr__(self, 'channelName', other.channelName)
        object.__setattr__(self, 'channelColor', other.channelColor)
        self.copyMetadataFrom(other)
        return self

@dataclass(frozen=True, kw_only=True)
class InputBinaryDef(ParameterDef, Metadata):
    binaryName: str
    binaryColor: int

@dataclass(frozen=True, kw_only=True)
class OutputBinaryDef(ParameterDef, Metadata):
    assignedParName: str|None = None
    binaryName: str|None = None
    binaryColor: int|None = None

    def assign(self, param: InputBinaryDef) -> OutputBinaryDef:
        if isinstance(param, InputBinaryDef):
            object.__setattr__(self, 'assignedParName', param.parName)
            object.__setattr__(self, 'binaryName', param.binaryName)
            object.__setattr__(self, 'binaryColor', param.binaryColor)
        else:
            raise TypeError('Expected param: str|InputBinaryDef')
        return self

    def makeNew(self, name: str, color: AnyColorDef) -> OutputBinaryDef:
        object.__setattr__(self, 'assignedParName', None)
        object.__setattr__(self, 'binaryName', name)
        object.__setattr__(self, 'binaryColor', _parse_color(color))
        object.__setattr__(self, 'componentCount', 1)
        return self

    def makeInt32(self) -> OutputBinaryDef:
        object.__setattr__(self, 'bitsPerComponent', 32)
        return self

    def makeUInt8(self) -> OutputBinaryDef:
        object.__setattr__(self, 'bitsPerComponent', 8)
        return self

    def copyFrom(self, other: OutputBinaryDef) -> OutputBinaryDef:
        object.__setattr__(self, 'assignedParName', other.assignedParName)
        object.__setattr__(self, 'binaryName', other.binaryName)
        object.__setattr__(self, 'binaryColor', other.binaryColor)
        self.copyMetadataFrom(other)
        return self

@dataclass(frozen=True, kw_only=True)
class InputTableDef(ParameterDef):
    tableDef: LimTableDataBase

@dataclass(frozen=True, kw_only=True)
class OutputTableDef(ParameterDef):
    assignedParName: str
    tableDef: LimTableDataBase

    def assign(self, param: InputTableDef) -> OutputTableDef:
        if isinstance(param, InputTableDef):
            object.__setattr__(self, 'assignedParName', param.parName)
            object.__setattr__(self, 'tableDef', param.tableDef)
        else:
            raise TypeError('Expected param: str|InputTableDef')
        return self

    def makeEmpty(self, name: str) -> OutputTableDef:
        object.__setattr__(self, 'assignedParName', None)
        self.tableDef.setTableName(name)
        self.tableDef.removeAllCols()
        return self

    def makeNew(self, name: str, param: InputTableDef|None = None) -> OutputTableDef:
        self.makeEmpty(name)
        if param is not None:
            if isinstance(param, InputTableDef):
                object.__setattr__(self, 'tableDef', param.tableDef)
            else:
                raise TypeError('Expected param: str|InputTableDef')
        else:
            self.withLoopCols()
        return self

    def withLoopCols(self) -> OutputTableDef:
        for loop in self.loopDefList:
            self._withColumn("int", f"{loop.name}Index", id=f"_loop{loop.name}Index", meta=dict(loopName=loop.name, loopType=int(loop.type)))
        return self

    def withEntityCol(self) -> OutputTableDef:
        self._withColumn("QString", "Entity", id="_Entity")
        return self

    def withObjectCols(self) -> OutputTableDef:
        self._withColumn("QString", "Entity", id="_Entity")
        self._withColumn("int", "ObjectId", id="_ObjId")
        return self

    def withObject3dCols(self) -> OutputTableDef:
        self._withColumn("QString", "Entity", id="_Entity")
        self._withColumn("int", "ObjectId", id="_ObjId3d")
        return self

    def withIntCol(self, title: str, unit: str|None = None, feature:str|None = None, id: str|None = None) -> OutputTableDef:
        return self._withColumn("int", title, unit, feature, id)

    def withFloatCol(self, title: str, unit: str|None = None, feature:str|None = None, id: str|None = None) -> OutputTableDef:
        return self._withColumn("double", title, unit, feature, id)

    def withStringCol(self, title: str, unit: str|None = None, feature:str|None = None, id: str|None = None) -> OutputTableDef:
        return self._withColumn("QString", title, unit, feature, id)

    def _withColumn(self, decltype: str, title: str, unit: str|None = None, feature:str|None = None, id: str|None = None, meta: dict[str, any]|None = None) -> OutputTableDef:
        if id is None:
            id = f'{self.parentNode.uuid}.{self.parentNode.defaultName}.{feature}' if feature is not None else f'{self.parentNode.uuid}.{self.parentNode.defaultName}.{title}'
        if meta is None:
            meta = dict()
        meta.update(dict(decltype=decltype, title=title))
        if unit is not None:
            meta["units"] = unit
        if feature is not None:
            meta["feature"] = feature
        self.tableDef.insertCol(id, [], meta)
        return self

    def copyFrom(self, other: OutputTableDef) -> OutputTableDef:
        object.__setattr__(self, 'assignedParName', other.assignedParName)
        object.__setattr__(self, 'tableDef', other.tableDef)
        return self

## Param data classes

@dataclass(frozen=True, kw_only=True)
class ArrayData:
    data: NumpyArray|None

    def setData(self, new_data: NumpyArray|None) -> None:
        object.__setattr__(self, 'data', new_data)

@dataclass(frozen=True, kw_only=True)
class RecordedData:
    recdata: LimTableDataBase|None

    def _copyRecordedDataFrom(self, other: RecordedData) -> None:
        col_ids = other.recdata.colIdList
        col_data = other.recdata.colData(col_ids)
        self.recdata.setColData(col_ids, col_data)


@dataclass(frozen=True, kw_only=True)
class InputChannelData(ParameterDef, Metadata, ArrayData, RecordedData):
    pass

@dataclass(frozen=True, kw_only=True)
class OutputChannelData(ParameterDef, Metadata, ArrayData, RecordedData):
    def copyRecordedDataFrom(self, other: RecordedData) -> None:
        self._copyRecordedDataFrom(other)


@dataclass(frozen=True, kw_only=True)
class InputBinaryData(ParameterDef, Metadata, ArrayData, RecordedData):
    pass

@dataclass(frozen=True, kw_only=True)
class OutputBinaryData(ParameterDef, Metadata, ArrayData, RecordedData):
    def copyRecordedDataFrom(self, other: RecordedData) -> None:
        self._copyRecordedDataFrom(other)

@dataclass(frozen=True, kw_only=True)
class InputTableData(ParameterDef, RecordedData):
    data: LimTableDataBase

    def colArray(self, cols: MultiColSpecifier|None = None) -> list[np.ndarray]:
        return self.data.colArray(cols)

@dataclass(frozen=True, kw_only=True)
class OutputTableData(ParameterDef, RecordedData):
    data: LimTableDataBase|None

    def withColDataFrom(self, other: InputTableData) -> OutputTableData:
        col_ids = list(filter(lambda id: not id.startswith('_loop'), other.data.colIdList))
        col_data = other.data.colData(col_ids)
        self.data.setColData(col_ids, col_data)
        return self

    def withColData(self, cols: MultiColSpecifier, data: MultiColData) -> OutputTableData:
        self.data.setColData(cols, data)
        return self

    def copyRecordedDataFrom(self, other: RecordedData) -> None:
        self._copyRecordedDataFrom(other)

    def copyFrom(self, other: RecordedData) -> None:
        assert isinstance(other, OutputTableData), "Unexpected argument type"
        if self.data and other.data:
            col_ids = other.data.colIdList
            col_data = other.data.colData(col_ids)
            self.data.setColData(col_ids, col_data)
            self.copyRecordedDataFrom(other)

@dataclass
class Program:
    allLoopDefs: list[LoopDef]
    overLoops: list[str] = field(default_factory=list, init=False)

    def overZStack(self) -> Program:
        for loop in self.allLoopDefs:
            if loop.type == ExperimentLoopType.loopTypeZStack and loop.name not in self.overLoops:
                self.overLoops.append(loop.name)
        return self

    def overTimeLapse(self) -> Program:
        for loop in self.allLoopDefs:
            if loop.type == ExperimentLoopType.loopTypeTLapse and loop.name not in self.overLoops:
                self.overLoops.append(loop.name)
        return self

    def overMultiPoint(self) -> Program:
        for loop in self.allLoopDefs:
            if loop.type == ExperimentLoopType.loopTypeXYSite and loop.name not in self.overLoops:
                self.overLoops.append(loop.name)
        return self

AnyInDef: TypeAlias = InputChannelDef|InputBinaryDef|InputTableDef
AnyOutDef: TypeAlias = OutputChannelDef|OutputBinaryDef|OutputTableDef
AnyInData: TypeAlias = InputChannelData|InputBinaryData|InputTableData
AnyOutData: TypeAlias = OutputChannelData|OutputBinaryData|OutputTableData

@dataclass
class ReduceProgram(Program):
    pass

@dataclass
class TwoPassProgram(Program):
    pass

@dataclass(kw_only=True)
class RunContext:
    inpFilename: str
    outFilename: str
    inpParameterCoordinates: tuple[tuple[int]]
    outCoordinates: tuple[int]
    programCoordinateIndexes: tuple[int]|None
    programPass: int
    finalCall: bool

    @property
    def shouldAbort(self) -> bool:
        try:
            return self._should_abort()
        except AttributeError:
            return False

def _parse_color(color: AnyColorDef) -> int:
    if type(color) == int:
        return color & 0xFFFFFF
    elif type(color) == str and len(color) == 7 and color[0] == '#':
        return int(color[1:], 16)
    elif type(color) == tuple:
        return (color[0] << 16) + (color[1] << 8) + color[2]
    else:
        return 0

###############################################################################
## Out-process
###############################################################################

@dataclass
class OutputRequest:
    inp: tuple[AnyInDef]
    out: tuple[AnyOutDef]

@dataclass
class BuildRequest:
    loops: list[LoopDef]

@dataclass
class RunRequest:
    inp: tuple[AnyInData]
    out: tuple[AnyOutData]
    ctx: dict[str, Any]
    shm: dict[str, dict]

class ChildProcessError(Exception):
    pass

    def __str__(self) -> str:
        return "\n" + self.args[0]

    def __repr__(self) -> str:
        return "\n" + self.args[0]

class CalledProcessError(subprocess.CalledProcessError):
    def __repr__(self) -> str:
        str_repr = "Exited code %d." % (self.returncode)
        if self.cmd:
            str_repr += "\n  From: %s" % (self.cmd)
        if self.stdout:
            str_repr += "\n%s" % (self.stdout.decode())
        if self.stderr:
            str_repr += "\n%s" % (self.stderr.decode())
        return str_repr

def ensure_child_process_alive(child_process: object, parent_connection: object, executable: str, child_code: str) -> tuple[object, object]:
    if isinstance(child_process, subprocess.Popen):
        try:
            print("Checking child process alive...")
            child_process.communicate(timeout=0)
        except subprocess.TimeoutExpired as _:
            print("Child process is alive!")
            return child_process, parent_connection
    return start_child_process(executable, child_code)

def start_child_process(executable: str, child_code: str) -> tuple[object, object]:
    from multiprocessing import Pipe
    TIMEOUT = 0.25
    parent_connection, child_connection = Pipe()

    python_home = os.path.dirname(executable)
    env = os.environ.copy()
    env["PYTHONHOME"] = python_home
    if "PYTHONPATH" in env:
        env.pop("PYTHONPATH")
    env["PATH"] = f"{python_home};{env['PATH']}"

    print("Creating child process...")
    child_process = subprocess.Popen([executable, '-', str(child_connection.fileno())], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)

    print("Passing the script to the child process...")
    try:
        stdout, stderr = child_process.communicate(child_code.encode(), timeout=TIMEOUT)
        raise CalledProcessError(child_process.returncode, executable, stdout, stderr)

    except subprocess.TimeoutExpired as _:
        pass

    print("Waiting for the child process to be ready...")
    while not parent_connection.poll(TIMEOUT):
        try:
            stdout, stderr = child_process.communicate(timeout=0)
            raise CalledProcessError(child_process.returncode, executable, stdout, stderr)

        except subprocess.TimeoutExpired as _:
            pass

    if parent_connection.recv() != "CHILD PROCESS READY":
        raise RuntimeError("Child process not ready")

    print("Child process ready and waiting for data!")

    child_connection._handle = None
    return child_process, parent_connection

def shutdown_child_process(child_process: object) -> str:
    child_process.kill()

    print("Waiting for child process to finish...")
    stdout, stderr = child_process.communicate()

    print("Child finished!")
    return "Child process finished with exit status %d.\nOutput:\n%s\nError:\n%s" % (child_process.returncode, stdout.decode(), stderr.decode())

def child_main(
        run: Callable[[tuple[AnyInData], tuple[AnyOutData], RunContext], Exception|None],
        output: Callable[[tuple[AnyInDef], tuple[AnyOutDef]], None]|None = None,
        build: Callable[[list[LoopDef]], Exception|None]|None = None,
    ) -> None:
    import os, sys, traceback
    from multiprocessing.connection import PipeConnection
    from multiprocessing.reduction import steal_handle

    # Since mamba activate is not called add Library\bin to the PATH manually
    library_bin = os.path.join(os.path.dirname(sys.executable), "Library", "bin")
    if os.path.isdir(library_bin):
        os.add_dll_directory(library_bin)
        os.environ["PATH"] = f"{library_bin};{os.environ.get('PATH', '')}"

    connection = PipeConnection(steal_handle(os.getppid(), int(sys.argv[1])))
    connection.send("CHILD PROCESS READY")
    while True:
        try:
            request = connection.recv()
        except Exception as e:
            connection.send(ChildProcessError("".join(traceback.format_exception(e))))
        if isinstance(request, OutputRequest) and output is not None:
            try:
                output(request.inp, request.out)
            except Exception as e:
                connection.send(ChildProcessError("".join(traceback.format_exception(e))))
            else:
                connection.send(request.out)
        elif isinstance(request, BuildRequest) and build is not None:
            try:
                ret = build(request.loops)
            except Exception as e:
                connection.send(ChildProcessError("".join(traceback.format_exception(e))))
            else:
                connection.send(ret)
        elif isinstance(request, RunRequest) and run is not None:
            try:
                _child_run(run, request.inp, request.out, request.ctx, request.shm)
            except Exception as e:
                connection.send(ChildProcessError("".join(traceback.format_exception(e))))
            else:
                connection.send(request.out)
        else:
            break

def _child_run(
        node_run: Callable[[tuple[AnyInData], tuple[AnyOutData], RunContext], Exception|None],
        inp: tuple[AnyInData], out: tuple[AnyOutData],
        ctx: RunContext,
        shm: dict
    ) -> Exception|None:
    from multiprocessing.shared_memory import SharedMemory
    par_sh_mem = {}
    for item in (inp + out):
        if isinstance(item, ArrayData) and item.parName in shm:
            sh_mem = SharedMemory(name=shm[item.parName]['name'], create=False)
            item.setData(np.ndarray(shm[item.parName]['shape'], shm[item.parName]['dtype'], buffer=sh_mem.buf))
            par_sh_mem[item.parName] = sh_mem

    try:
        node_run(inp, out, ctx)

    except Exception as _:
        raise

    finally:
        for item in (inp + out):
            if isinstance(item, ArrayData) and item.parName in par_sh_mem:
                item.setData(None)
                par_sh_mem[item.parName].close()

def parent_output(inp: tuple[AnyInDef], out: tuple[AnyOutDef], process: object, connection: object) -> None:
    connection.send(OutputRequest(inp=inp, out=out))
    ret = connection.recv()
    if isinstance(ret, Exception):
        raise ret
    else:
        for out_item, ret_item in zip(out, ret):
            out_item.copyFrom(ret_item)

def parent_build(loops: list[LoopDef], process: object, connection: object) -> Program|None:
    connection.send(BuildRequest(loops=loops))
    ret = connection.recv()
    if isinstance(ret, Exception):
        raise ret
    else:
        return ret

def parent_run(inp: tuple[AnyInData], out: tuple[AnyOutData], ctx: RunContext, process: object, connection: object) -> None:
    from multiprocessing.shared_memory import SharedMemory
    par_sh_mem, shm = {}, {}
    src_arrays = {}
    for item in (inp + out):
        if isinstance(item, ArrayData) and item.data is not None:
            src_arrays[item.parName] = item.data
            sh_mem = SharedMemory(create=True, size=item.data.nbytes)
            shape, dtype = item.data.shape, item.data.dtype
            tmp = np.ndarray(shape, dtype, buffer=sh_mem.buf)
            tmp[:] = item.data
            item.setData(None)
            shm[item.parName] = dict(name=sh_mem.name, shape=shape, dtype=dtype)
            par_sh_mem[item.parName] = sh_mem

    connection.send(RunRequest(inp=inp, out=out, ctx=RunContext(**asdict(ctx)), shm=shm))

    while not connection.poll(0.1):
        if ctx.shouldAbort:
            print("Aborting - killing child process...")
            process.kill()
            return

    ret = connection.recv()
    if isinstance(ret, Exception):
        raise ret

    for item in inp:
        if isinstance(item, ArrayData) and item.parName in par_sh_mem:
            sh_mem = par_sh_mem[item.parName]
            item.setData(src_arrays.pop(item.parName, None))
            sh_mem.close()

    for item, ret_item in zip(out, ret):
        if isinstance(item, ArrayData) and item.parName in par_sh_mem:
            sh_mem = par_sh_mem[item.parName]
            src_arrays.pop(item.parName, None)
            tmp = np.copy(np.ndarray(shm[item.parName]['shape'], shm[item.parName]['dtype'], buffer=sh_mem.buf))
            item.setData(tmp)
            tmp = None
            sh_mem.close()
        elif isinstance(item, OutputTableData):
            item.copyFrom(ret_item)

def separateLabeledImage(src):
    if not isinstance(src, np.ndarray):
        raise TypeError("Expected 2-dimensional array")
    if src.ndim != 2:
        raise TypeError("Expected 2-dimensional array")

    padded = np.pad(src, (1,1))
    shape = (src.shape[0], src.shape[1], 3, 3)
    strides = padded.strides + padded.strides

    windows = as_strided(padded, shape=shape, strides=strides)
    max_values = np.max(windows, axis=(2, 3))
    return np.where(src < max_values, 0, src)

def separateLabeledImage3d(src: np.ndarray) -> np.ndarray:
    if not isinstance(src, np.ndarray):
        raise TypeError("Expected 3-dimensional array")
    if src.ndim != 3:
        raise TypeError("Expected 3-dimensional array")

    padded = np.pad(src, ((1, 1), (1, 1), (1, 1)))
    shape = (src.shape[0], src.shape[1], src.shape[2], 3, 3, 3)
    strides = padded.strides + padded.strides

    windows = as_strided(padded, shape=shape, strides=strides)
    max_values = np.max(windows, axis=(3, 4, 5))
    return np.where(src < max_values, 0, src)