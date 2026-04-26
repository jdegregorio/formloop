import importlib
import inspect
import pydoc
import traceback
from pathlib import Path

from agents import apply_diff, function_tool, RunContextWrapper

from .common import RunContext

MAX_CHARS = 12_000

class WorkspaceEditor:
    def __init__(self, root: Path | str):
        self.root = Path(root).resolve()

    def _path(self, relative_path: str) -> Path:
        path = (self.root / relative_path).resolve()
        if not str(path).startswith(str(self.root)):
            raise ValueError("Path escapes workspace")
        return path

    async def create_file(self, operation):
        path = self._path(operation.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        content = apply_diff("", operation.diff, create=True)
        path.write_text(content)
        return {"status": "completed", "output": f"Created {operation.path}"}

    async def update_file(self, operation):
        path = self._path(operation.path)
        current = path.read_text()
        new_content = apply_diff(current, operation.diff)
        path.write_text(new_content)
        return {"status": "completed", "output": f"Updated {operation.path}"}

    async def delete_file(self, operation):
        path = self._path(operation.path)
        path.unlink()
        return {"status": "completed", "output": f"Deleted {operation.path}"}

@function_tool
def test_build_model(ctx: RunContextWrapper[RunContext]) -> str:
    """Test the current model.py to ensure it builds correctly. Call this after editing model.py."""
    model_path = ctx.context.source_dir / "model.py"
    if not model_path.exists():
        return "Error: model.py does not exist yet."
    
    build_dir = ctx.context.source_dir / "test_build"
    build_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        from ..runtime.cad_cli import cad_build
        result = cad_build(
            model_path=model_path,
            output_dir=build_dir,
            timeout=ctx.context.timeouts.cad_build,
        )
        return f"Build successful! Volume: {result.volume}, Bounding Box: {result.bounding_box.size}"
    except Exception as e:
        from ..runtime.subprocess import CliError
        if isinstance(e, CliError):
            err_msg = f"Build failed with exit code {e.returncode}.\n"
            if e.stderr:
                err_msg += f"Stderr:\n{e.stderr}\n"
            if e.stdout:
                err_msg += f"Stdout:\n{e.stdout}\n"
            if e.cli_error_traceback:
                err_msg += f"Traceback:\n{e.cli_error_traceback}\n"
            return err_msg
        return f"Build failed:\n{traceback.format_exc()}"

@function_tool
def python_help(target: str) -> str:
    """
    Return Python help/docs for an installed module, class, function, or method.

    Examples:
    - cadquery.Workplane
    - build123d.Box
    - trimesh.load
    - pathlib.Path.glob
    """
    obj = pydoc.locate(target)

    if obj is None:
        try:
            obj = importlib.import_module(target)
        except Exception as e:
            return f"Could not locate or import {target!r}: {type(e).__name__}: {e}"

    try:
        doc = pydoc.render_doc(obj, renderer=pydoc.plaintext)
    except Exception as e:
        return f"Located {target!r}, but could not render docs: {type(e).__name__}: {e}"

    return doc[:MAX_CHARS]

@function_tool
def python_inspect(target: str) -> str:
    """
    Return signature, docstring, file location, and source snippet for a Python object.
    """
    obj = pydoc.locate(target)
    if obj is None:
        return f"Could not locate {target!r}"

    parts = [f"Target: {target}"]

    try:
        parts.append(f"Type: {type(obj)}")
    except Exception:
        pass

    try:
        parts.append(f"Signature: {inspect.signature(obj)}")
    except Exception:
        parts.append("Signature: <unavailable>")

    try:
        parts.append(f"File: {inspect.getfile(obj)}")
    except Exception:
        pass

    doc = inspect.getdoc(obj)
    if doc:
        parts.append("\nDocstring:\n" + doc[:4000])

    try:
        source = inspect.getsource(obj)
        parts.append("\nSource:\n" + source[:6000])
    except Exception:
        pass

    return "\n".join(parts)
