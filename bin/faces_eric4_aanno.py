#!python
import sys
sys.path.pop(0)
sys.path.pop(0)
sys.path.insert(0, "/home/tpasch/project/faces-project")
sys.path.insert(1, "/home/tpasch/mypython/lib64/python2.5/site-packages")
print sys.path
from faces.gui.plangui import main
sys.exit(main())
