h=open('/home/claude/calc/index.html').read()
i=h.index('/*ENDBACKUP*/')+len('/*ENDBACKUP*/')
h=h[:i]+'\n'+open('/home/claude/backup/sheets_fn.js').read()+h[i:]
open('/home/claude/calc/index.html','w').write(h);print('sheets ok')
