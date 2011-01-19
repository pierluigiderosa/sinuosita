#!/usr/bin/env python

#%Module
#%  description: Calculates the ortho lines.
#%  keywords: Ortho
#%End

#%option
#% key: map
#% type: string
#% gisprompt: old,vector,vector
#% key_desc: name
#% description: Name of fiume vector map 
#% required: yes
#%end

#%option
#% key: sponde
#% type: string
#% gisprompt: old,vector,vector
#% key_desc: name
#% description: Name of sponde vector map 
#% required: yes
#%end

#%option
#% key: distanza
#% type: double
#% description: distanza di splitting
#% required: yes
#%end

#%option
#% key: semilarghezza
#% type: double
#% description: semilarghezza
#% required: yes
#%end
import os
import sys
import math

#~ from grass.lib import grass as grasslib
#~ from grass.lib import vector as grassvect
import grass.script as grass

if "GISBASE" not in os.environ:
	print "You must be in GRASS GIS to run this program."
	sys.exit(1)

def main():
	reticolo = options['map']	
	distanza = options['distanza']
	sponde = options['sponde']
	semilargh=int(options['semilarghezza'])
	#~ calcolo la lunghezza del tratto fluviale
	lunghezza=float(grass.read_command('v.to.db',map=reticolo,option='length',colum='pp',flags='p').split('\n')[1].split('|')[1])
	line_cat=int(grass.read_command('v.to.db',map=reticolo,option='length',colum='pp',flags='p').split('\n')[1].split('|')[0])
	#~ determino il numero di passi
	npassi=int(lunghezza/int(distanza)) 
	#~ npassi e anche la variabile che conta il numero vero di sezioni trasversali
	f = open ( '/tmp/cvs.txt', 'w' )
	step=int(distanza)
	#~ creo i punti estremi delle sezioni trasversali
	#~ creo il file per v.segment
	for i in range(npassi):
		f.write('P %s %s %s %s\n'%(i,line_cat,step,semilargh))
		f.write('P %s %s %s -%s\n'%(i,line_cat,step,semilargh))
		step=step+int(distanza)
	f.close()
	grass.run_command('v.segment',input=reticolo,output='punti',overwrite=True,file='/tmp/cvs.txt')
	#~ creo il file di punti posti sull'asse alveo che conterra i valori di larghezza chiamato PUNTI_ASSE
	f1 = open ( '/tmp/cvs1.txt', 'w' )
	step=int(distanza)
	for i in range(npassi):
		f1.write('P %s %s %s\n'%(i,line_cat,step))
		step=step+int(distanza)
	f1.close()
	grass.run_command('v.segment',input=reticolo,output='punti_asse',overwrite=True,file='/tmp/cvs1.txt')
	grass.run_command('v.db.addtable', map = 'punti_asse', layer = '1' , columns ='cat integer')
	grass.run_command('v.db.addcol', map = 'punti_asse', layer = '1' , columns ='largh double')
	#~ os.remove('csv.txt')
	f = open ( '/tmp/line.txt', 'w' )
	step=int(distanza)
	#~ creo il file per v.in.ascii
	for i in range(npassi): 
		grass.run_command('v.extract', input = 'punti' , output = 'punti%d'%(i) , layer = '1' , list = i , new = '-1',overwrite=True)
		grass.run_command('v.category', input = 'punti%d'%(i) , output = 'puntidel%d'%(i) , option = 'del' , type = 'point',overwrite=True)
		grass.run_command('v.category', input = 'puntidel%d'%(i) , output = 'puntiadd%d'%(i) , option = 'add' , type = 'point',overwrite=True)
		line=grass.read_command('v.to.db',map='puntiadd%d'%(i),option='coor',colum='pp',flags='p')
		xstart=float(line.split('\n')[1].split('|')[1])
		ystart=float(line.split('\n')[1].split('|')[2])
		xend=float(line.split('\n')[2].split('|')[1])
		yend=float(line.split('\n')[2].split('|')[2])		
		f.write('L 2 1\n')
		f.write('%s %s\n'%(xstart,ystart))
		f.write('%s %s\n'%(xend,yend))
		f.write('1 %s\n'%(i))
		grass.run_command('g.remove' , vect = 'punti%d,puntidel%d,puntiadd%d'%(i,i,i))
		step=step+int(distanza)
	f.close()
	grass.run_command('v.in.ascii',flags='n',input='/tmp/line.txt',output='linee',overwrite=True,format='standard')
	#~ predispongo il vettoriale linee ad accettare le larghezze
	grass.run_command('v.db.addtable', map = 'linee', layer = '1' , columns ='cat integer')
	#~ grass.run_command('v.db.addcol', map = 'linee', layer = '1' , columns ='largh double')
	#~ devo occuparmi di calcolare solo i tratti lunghi di ogni segmento
	grass.run_command('v.overlay', ainput='linee', atype='line', binput=sponde, output='linee_clip', operator='and',overwrite=True)
	
	#~ calcolo tutte le lunghezze dei vari segmentini
	lunghezze=grass.read_command('v.to.db',flags='p',column='pp',map='linee_clip',option='length').split('\n')
	for sezione in range(npassi):
		cat_dup=grass.read_command('db.select', flags = 'c' , table = 'linee_clip' , sql = "SELECT cat FROM linee_clip WHERE a_cat=%d"%(sezione)).split('\n')
		cat_dup.remove('')
		lungh_parziali=list()	
		for j in cat_dup:
			lungh_parziali.append(float(lunghezze[int(j)].split('|')[1]))			
		grass.write_command('db.execute',stdin = 'UPDATE punti_asse SET largh=%f WHERE cat=%d'%(max(lungh_parziali),sezione))
		
	#~ creazione di un vettoriale ortogonale asse alveo perfettamente ritagliato alle sponde
	

	
if __name__ == "__main__":
	options, flags = grass.parser()
	sys.exit(main())
