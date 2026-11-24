"""Build a separate prototype against the reviewed native opening callback."""
from hashlib import file_digest
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import json
import subprocess
import sys

def build(source, output, allocation):
    expected = json.loads(allocation.read_text())['native_parent']
    with source.open('rb') as stream:
        if file_digest(stream,'sha256').hexdigest() != expected:
            raise ValueError('Unexpected native input')
    here = Path(__file__).parent
    export = '--add-exports=java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED'
    target = 'forge/ai/PlayerControllerAi.class'
    helper = 'forge/ai/validation/IndependentOpening.class'
    with TemporaryDirectory() as work, ZipFile(source) as original:
        tmp = Path(work)
        subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main',export,'-cp',str(source),
                        '-d',work,str(here/'Install.java'),str(here/'IndependentOpening.java')],check=True)
        (tmp/'in').write_bytes(original.read(target))
        subprocess.run(['java',export,'-cp',work,'Install',str(tmp/'in'),str(tmp/'out')],check=True)
        with ZipFile(output,'x') as out:
            for item in original.infolist():
                out.writestr(item,(tmp/'out').read_bytes() if item.filename == target else original.read(item))
            out.writestr(ZipInfo(helper,(2026,11,24,0,0,0)),(tmp/helper).read_bytes(),ZIP_DEFLATED)


if __name__ == '__main__':
    build(*map(Path,sys.argv[1:]))
