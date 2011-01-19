#!/usr/bin/env python

#%Module
#%  description: Calculata la sinuosita di un alveo.
#%  keywords: Ortho
#%End

#%option
#% key: asse_alveo
#% type: string
#% gisprompt: old,vector,vector
#% key_desc: asse_alveo
#% description: vettoriale asse del alveo 
#% required: yes
#%end

#%option
#% key: asse_pianura
#% type: string
#% gisprompt: old,vector,vector
#% key_desc: asse_pianura
#% description: vettoriale asse pianura 
#% required: yes
#%end

#%option
#% key: passo
#% type: double
#% description: distanza di splitting
#% required: yes
#%end

#%option
#% key: semilarghezza
#% type: double
#% description: semilarghezza valore INTERO
#% required: yes
#%end

import os
import sys
import math
import grass.script as grass

if "GISBASE" not in os.environ:
	print "You must be in GRASS GIS to run this program."
	sys.exit(1)

def main():
	alveo = options['asse_alveo']
	pianura =options['asse_pianura']	
	passo = int(options['passo'])
	semiL=int(options['semilarghezza'])
	
	#~ individuo la categoria del fiume
	catAlveo=grass.read_command('v.category',input=alveo,option='print').split('\n')
	catAlveo.remove('')
	#~ individuo tutti le category degli elementi del asse pianura in modo da ciclare per ognuno di essi
	categorie=grass.read_command('v.category',input=pianura,option='print').split('\n')
	categorie.remove('')
	
	#~ metto per debugging
	#~ categorie=[1]
	
	#~ file per il salvataggio dei dati asse pianura
	f3 = open ( '/tmp/risultati.csv', 'w' )
	
	#~ costruisco il vettoriale tratti che contiene i tratti output
	grass.run_command('v.edit', tool='create', map='tratti',overwrite=True)
	grass.run_command('v.db.addtable',map='tratti',columns='id INT, fcat INT, tcat INT, sp INT, cost DOUBLE, tdist DOUBLE, sinuos DOUBLE')
	
	#~ costruisco il vettoriale punti che contiene output
	grass.run_command('v.edit', tool='create', map='puntiSinuos',overwrite=True)
	grass.run_command('v.db.addtable',map='puntiSinuos',columns='id INT, prog DOUBLE, sinuos DOUBLE')
	
	
	#~ determino il punto piu a monte asse fiume
	grass.write_command('v.segment', stdin = 'P 1000 %s 0' %(int(catAlveo[0])),overwrite=True,input=alveo,output='puntoMonte')
	
	#~ variabile che conta la distanza totale lungo asse pianura
	lungTrattoPrec=0	
	
	#~ per ogni categoria dell asse pianura eseguo il calcolo della sinuosita
	for cat in categorie:
		cat=int(cat)
		grass.run_command('v.extract', input = pianura , output = 'tratto_pianura', layer = '1' , list = cat , new = '-1',overwrite=True)
		lunghezza=float(grass.read_command('v.to.db',map='tratto_pianura',option='length',colum='pp',flags='p').split('\n')[1].split('|')[1])
		#~ determino il numero di passi
		#~ npassi e anche la variabile che conta il numero vero di sezioni trasversali
		npassi=int(lunghezza/passo)
		
		
		#~ metto questa per debugging - da togliere
		#~ npassi=2
		
		step=0
		#~ step1 e la variabile che individua la progressiva al passo seguente
		step1=passo
		

			
		for i in range(npassi):
			f1 = open ( '/tmp/line1.txt', 'w' )
			f2 = open ( '/tmp/line2.txt', 'w' )
			#~ definizione delle partenze
			grass.write_command('v.segment', stdin = 'P %s %s %s -%s \n P %s %s %s %s' % (i,cat,step,semiL,i+1,cat,step,semiL),overwrite=True,input=pianura,output='estremi_monte');
			line_m=grass.read_command('v.to.db',map='estremi_monte',option='coor',colum='pp',flags='p')
			xstart_m=float(line_m.split('\n')[1].split('|')[1])
			ystart_m=float(line_m.split('\n')[1].split('|')[2])
			xend_m=float(line_m.split('\n')[2].split('|')[1])
			yend_m=float(line_m.split('\n')[2].split('|')[2])
			f1.write('L 2 1\n')
			f1.write('%s %s\n'%(xstart_m,ystart_m))
			f1.write('%s %s\n'%(xend_m,yend_m))
			f1.write('1 2\n')
			f1.close()
			grass.run_command('v.in.ascii',flags='n',input='/tmp/line1.txt',output='linea_monte',overwrite=True,format='standard')
			grass.run_command('v.patch',input=alveo+',linea_monte',output='monte_patch',overwrite=True)
			grass.run_command('v.clean',input='monte_patch',output='monte_patch1',error='partenze_1',overwrite=True,tool='break')
			grass.run_command('v.category', input = 'partenze_1' , output = 'partenze' , type = 'point' , option = 'add' , step = '1')
			#~ definizione degli arrivi
			grass.write_command('v.segment', stdin = 'P %s %s %s -%s \n P %s %s %s %s' % (i,cat,step1,semiL,i+1,cat,step1,semiL),overwrite=True,input=pianura,output='estremi_valle');
			line_v=grass.read_command('v.to.db',map='estremi_valle',option='coor',colum='pp',flags='p')
			xstart_v=float(line_v.split('\n')[1].split('|')[1])
			ystart_v=float(line_v.split('\n')[1].split('|')[2])
			xend_v=float(line_v.split('\n')[2].split('|')[1])
			yend_v=float(line_v.split('\n')[2].split('|')[2])
			f2.write('L 2 1\n')
			f2.write('%s %s\n'%(xstart_v,ystart_v))
			f2.write('%s %s\n'%(xend_v,yend_v))
			f2.write('1 3\n')
			f2.close()
			grass.run_command('v.in.ascii',flags='n',input='/tmp/line2.txt',output='linea_valle',overwrite=True,format='standard')	
			grass.run_command('v.patch',input=alveo+',linea_valle',output='valle_patch',overwrite=True)
			grass.run_command('v.clean',input='valle_patch',output='valle_patch1',error='arrivi_1',overwrite=True,tool='break')	
			#~ metto una cat molto elevata agli arrivi per non confonderli con le partenze
			grass.run_command('v.category', input = 'arrivi_1' , output = 'arrivi' , type = 'point' , option = 'add' , step = '1',cat='100')	
			
			#~ individuo le category dei punti di partenza e arrivo
			cat_part=grass.read_command('v.category', input = 'partenze' , type='point', option = 'print').split('\n')
			cat_arr=grass.read_command('v.category', input = 'arrivi' , type='point', option = 'print').split('\n')
			cat_part.remove('')
			cat_arr.remove('')

			#~ unisco le partenze con gli arrivi per poter fare il v.net 
			grass.run_command('v.patch',input='arrivi,partenze',output='partenze_arrivi',overwrite=True)
			grass.run_command('v.net', overwrite=True, input=alveo, points='partenze_arrivi', output='part_arr_connesso', operation='connect', thresh='50')
			
			totale_lung=[]
			elem=0
			for p in cat_part:
				p=int(p)
				for a in cat_arr:
					a=int(a)
					#~ per fare il percorso
					grass.write_command('v.net.path', input = 'part_arr_connesso' , out = 'mypath' , type = 'line', stdin='1 %s %s'%(p,a),overwrite=True)
					totale_lung.append({'lunghezza':float(grass.read_command('v.to.db',map='mypath',option='length',colum='pp',flags='p').split('\n')[1].split('|')[1]),'partenza':p,'arrivo':a})
			#~ questo ciclo for individia l'elemento della lista che fornisce la massima lunghezza
			for j in range(len(totale_lung)):
				if totale_lung[j]['lunghezza'] > totale_lung[0]['lunghezza'] : elem=j
			
			#~ questa procedura associa la sinuosita al tratto di alveo considerato e li unisce in un unico vettoriale output del processo
			grass.write_command('v.net.path', input = 'part_arr_connesso' , out = 'tratto', type = 'line', stdin='1 %s %s'%(totale_lung[elem]['partenza'],totale_lung[elem]['arrivo']),overwrite=True)
			grass.write_command('db.execute',stdin = 'UPDATE tratto SET fdist=%f WHERE fcat=%d'%(totale_lung[elem]['lunghezza']/passo,totale_lung[elem]['partenza']))
			grass.write_command('db.execute',stdin = 'UPDATE tratto SET id=%d%d'%(cat,i)) #al campo id scrivo il tratto di riferimento  primo numero cat pianura e poi tratto
			grass.run_command('v.db.renamecol',map='tratto',column='fdist,sinuos')
			grass.run_command('v.patch',flags='ae',input='tratto',output='tratti',overwrite=True)
			
			#~ procedura per calcolare la progressiva rispetto al punto di partenza del fiume e scrivere gli output sul punto finale
			grass.run_command('v.extract', input = 'arrivi' , output = 'arriviOK', layer = '1' , list = int(totale_lung[elem]['arrivo']) , new = '-1',overwrite=True)
			grass.run_command('v.patch',input='arriviOK,puntoMonte',output='arriviOK_puntoMonte',overwrite=True)
			grass.run_command('v.net', overwrite=True, input=alveo, points='arriviOK_puntoMonte', output='netProgr', operation='connect', thresh='50')
			grass.write_command('v.net.path', input = 'netProgr' , out = 'mypath1' , type = 'line', stdin='1 1000 %s'%(int(totale_lung[elem]['arrivo'])),overwrite=True)
			distProgr=float(grass.read_command('v.to.db',map='mypath1',option='length',colum='pp',flags='p').split('\n')[1].split('|')[1])
			grass.run_command('v.db.addtable', map = 'arriviOK', layer = '1' , columns ='id INT, prog DOUBLE, sinuos DOUBLE')
			grass.write_command('db.execute',stdin = 'UPDATE arriviOK SET sinuos=%f'%(totale_lung[elem]['lunghezza']/passo))
			grass.write_command('db.execute',stdin = 'UPDATE arriviOK SET id=%d'%(i))
			grass.write_command('db.execute',stdin = 'UPDATE arriviOK SET prog=%f'%(distProgr))
			grass.run_command('v.patch',flags='ae',input='arriviOK',output='puntiSinuos',overwrite=True)
			
			#~ procedura per scrivere sul file csv i risultati della sinuosita rispetto asse pianura
			f3.write('%d,%f\n'%(step1+lungTrattoPrec,totale_lung[elem]['lunghezza']/passo))
						
			#~ alla fine del ciclo incremento le variabili contatori
			step=step+passo
			step1=step1+passo
		lungTrattoPrec=lunghezza+lungTrattoPrec
	grass.run_command('g.remove',flags='f',rast='out',vect='netProgr,arriviOK_puntoMonte,puntoMonte,mypath1,part_arr_connesso,arriviOK,tratto,tratto_pianura,estremi_monte,linea_monte,monte_patch,monte_patch1,estremi_valle,linea_valle,valle_patch,valle_patch1,partenze_1,arrivi_1,arrivi,partenze,mypath,partenze_arrivi');
	f3.close()
		

	
if __name__ == "__main__":
	options, flags = grass.parser()
	sys.exit(main())
