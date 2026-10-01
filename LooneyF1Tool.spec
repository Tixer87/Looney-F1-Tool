from PyInstaller.utils.hooks import collect_all
import tkinter
tkinter.Tcl().eval('info library')
datas,binaries,hiddenimports=collect_all('fastf1')
datas+=[('mapping/*.json','mapping'),('export/*.schema.json','export'),('config.json','.'),('icon.ico','.')]
a=Analysis(['gui_app.py'],pathex=[],binaries=binaries,datas=datas,hiddenimports=hiddenimports+['sseclient','dateutil.parser','jsonschema'],hookspath=[],runtime_hooks=[],excludes=[])
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,a.binaries,a.datas,[],name='LooneyF1Tool_1.9.1',debug=False,strip=False,upx=False,console=False,icon='icon.ico')