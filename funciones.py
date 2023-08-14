# Importamos las librerias necesarias, opencv y numpy
import numpy as np
import cv2
import math

# Funcion para calcular el angulo entre 3 puntos
def angle(s,e,f):
    v1 = [s[0]-f[0],s[1]-f[1]]
    v2 = [e[0]-f[0],e[1]-f[1]]
    ang1 = math.atan2(v1[1],v1[0])
    ang2 = math.atan2(v2[1],v2[0])
    ang = ang1 - ang2
    if (ang > np.pi):
        ang -= 2*np.pi
    if (ang < -np.pi):
        ang += 2*np.pi
    return ang*180/np.pi

# Funcion para encontrar el mayor contorno
def biggest_contour(contours):
	# Se inicializan las variables a 0
	max = 0
	hull = None
	cnt = None
	rect = None

	# Se recorren los contornos y se retorna el mayor
	for contour in contours:
		area = cv2.convexHull(contour)
		if cv2.contourArea(area) > max and cv2.contourArea(area) > 700:
			max = cv2.contourArea(area)
			hull = cv2.convexHull(contour, returnPoints = False)
			cnt = contour
			rect = cv2.boundingRect(contour)
	
	return hull, cnt, rect

# Funcion para encontrar defectos y pintar los diferentes modos
def defects(hull, cnt, rect, roi, paint_list, paint, fing, color, frame, show, type_paint):
	hull[::-1].sort(axis=0)
	defects = cv2.convexityDefects(cnt, hull)

	# Rectangulo que engloba el contorno
	pt1_ = (rect[0],rect[1])
	pt2_ = (rect[0]+rect[2],rect[1]+rect[3])
	if show:
		cv2.rectangle(roi,pt1_,pt2_,(0,255,255),3)

	# Si hay defectos, contamos los dedos
	if defects is not None:
		fingers = 0

		# Recorremos los defectos para contar cada dedo
		for i in range(len(defects)):
			s,e,f,d = defects[i,0]
			start = tuple(cnt[s][0])
			end = tuple(cnt[e][0])
			far = tuple(cnt[f][0])
			depth = d/256.0
			ang = angle(start,end,far)
			if depth > 1 and ang < 90:
				fingers += 1
				if show:
					cv2.line(roi,start,end,[255,0,0],2)
					cv2.circle(roi,far,5,[0,0,255],-1)

		# En caso de no haber dedos, y el punto más alto del contorno respecto a la mitad del contorno supera un umbral
		# damos por hecho que hay un dedo
		if fingers == 0:
			minY = (pt2_[1] - pt1_[1]) - cnt.min(axis=1)[0][1]
			if minY > 50:
				fingers = 1
		else:
			fingers += 1

		# Se pinta si está en modo pintar
		if paint:
			paint_list.append(cnt.min(axis=1)[0])
			for i in range(len(paint_list) - 1):
				if type_paint == 1:
					cv2.line(roi,paint_list[i],paint_list[i+1],[0,0,255],3)
				elif type_paint == 2:
					cv2.line(roi,paint_list[i],paint_list[i+1],[255,0,0],3)
				elif type_paint == 3:
					cv2.line(roi,paint_list[i],paint_list[i+1],[0,255,0],3)
				elif type_paint == 4:
					b, g, r = cv2.cvtColor(np.uint8([[[color, 255, 255]]]), cv2.COLOR_HSV2BGR)[0][0]
					cv2.line(roi,paint_list[i],paint_list[(i+1)%len(paint_list)],[int(b),int(g),int(r)],2)
					color = (color + 1) % 255

		# Se muestra el número de dedos si está en modo contar
		if fing:
			cv2.putText(frame,"N Dedos: " + str(fingers),(50,50),cv2.QT_FONT_NORMAL,1,(0,0,255),3)
			
		return fingers

# Funcion para detectar los gestos
def gestos(fingers, cnt_list, frame):
	# Comprueba si hay algun contorno en la lista
	check_cnt = False
	for cnt in cnt_list:
		if cnt is None:
			check_cnt = True
			break

	# Calcula el area del contorno
	if len(cnt_list) > 1 and not check_cnt:
		MAX_V = cnt_list[1].min(axis=1)[0]
		MIN_V = cnt_list[1].max(axis=1)[0]
		MAX_H = cnt_list[1].max(axis=0)[0]
		MIN_H = cnt_list[1].min(axis=0)[0]

		PMAX_V = cnt_list[0].min(axis=1)[0]
		PMIN_V = cnt_list[0].max(axis=1)[0]
		PMAX_H = cnt_list[0].max(axis=0)[0]
		PMIN_H = cnt_list[0].min(axis=0)[0]

	# Threshold para detectar el gesto
	thres = 1.5

	# Si hay un dedo en la lista, se calcula el gesto determinado
	if fingers == 0:
		cv2.putText(frame,"MANO CERRADA",(5,440),cv2.FONT_ITALIC,1,(255,0,0),2)
	elif fingers == 5:
		cv2.putText(frame,"MANO ABIERTA",(5,440),cv2.FONT_ITALIC,1,(255,0,0),2)

	if len(cnt_list) > 1 and not check_cnt:
		if (PMAX_V - MAX_V)[1] > thres:
			cv2.putText(frame,"{} DEDOS HACIA ARRIBA".format(fingers),(5,470),cv2.FONT_ITALIC,1,(255,0,0),2)
		elif (MIN_V - PMIN_V)[1] > thres:
			cv2.putText(frame,"{} DEDOS HACIA ABAJO".format(fingers),(5,470),cv2.FONT_ITALIC,1,(255,0,0),2)
		elif (PMAX_H - MAX_H)[0] > thres:
			cv2.putText(frame,"{} DEDOS HACIA LA IZQUIERDA".format(fingers),(5,470),cv2.FONT_ITALIC,1,(255,0,0),2)
		elif (MIN_H - PMIN_H)[0] > thres:
			cv2.putText(frame,"{} DEDOS HACIA LA DERECHA".format(fingers),(5,470),cv2.FONT_ITALIC,1,(255,0,0),2)

# Funcion para el menu inferior
def menu(frame, paint, fing, gests, show):
	# Se crea una franja inferior para el menu
	menu = np.zeros((110,frame.shape[1],3), np.uint8)
	menu[:,:] = (32,32,32)

	# Se crea todo el texto necesario con la informacion del menu

	# Salir
	cv2.putText(menu,"Q para salir del programa",(10,20),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,255,255),1)

	# Pintar
	cv2.putText(menu,"P para pintar:",(10,40),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,255,255),1)
	col_gest = 127
	if paint:
		cv2.putText(menu,"{}".format(paint),(130,40),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,0),1)
		if not gests and not fing and not show:
			cv2.putText(menu,"Colores disponibles:",(410,20),cv2.FONT_HERSHEY_SIMPLEX,0.5,(col_gest + 50,col_gest + 50,col_gest + 50),1)
			cv2.putText(menu,"1 para Rojo",(430,40),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,0,col_gest),1)
			cv2.putText(menu,"2 para Azul",(430,60),cv2.FONT_HERSHEY_SIMPLEX,0.5,(col_gest * 2,0,0),1)
			cv2.putText(menu,"3 para Verde",(430,80),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,col_gest,0),1)
			cv2.putText(menu,"4 para Multicolor",(430,100),cv2.FONT_HERSHEY_SIMPLEX,0.5,(col_gest,col_gest,col_gest),1)
	else:
		cv2.putText(menu,"{}".format(paint),(130,40),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,0,255),1)

	# Contar
	cv2.putText(menu,"C para contar el numero de dedos:",(10,60),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,255,255),1)
	if fing:
		cv2.putText(menu,"{}".format(fing),(305,60),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,0),1)
		if not gests and not paint and not show:
			cv2.putText(menu,"Se indicar el",(430,20),cv2.FONT_HERSHEY_SIMPLEX,0.5,(col_gest ,col_gest ,col_gest ),1)
			cv2.putText(menu,"numero de dedos",(430,40),cv2.FONT_HERSHEY_SIMPLEX,0.5,(col_gest ,col_gest,col_gest ),1)
			cv2.putText(menu,"segun los ",(430,60),cv2.FONT_HERSHEY_SIMPLEX,0.5,(col_gest ,col_gest ,col_gest ),1)
			cv2.putText(menu,"que se muestren",(430,80),cv2.FONT_HERSHEY_SIMPLEX,0.5,(col_gest ,col_gest ,col_gest ),1)
			cv2.putText(menu,"en camara",(430,100),cv2.FONT_HERSHEY_SIMPLEX,0.5,(col_gest ,col_gest ,col_gest ),1)
	else:
		cv2.putText(menu,"{}".format(fing),(305,60),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,0,255),1)

	# Detección
	cv2.putText(menu,"M para mostar la deteccion de la mano:",(10,80),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,255,255),1)
	if show:
		cv2.putText(menu,"{}".format(show),(345,80),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,0),1)
		if not gests and not paint and not fing:
			cv2.putText(menu,"Se muestra",(430,20),cv2.FONT_HERSHEY_SIMPLEX,0.5,(col_gest ,col_gest ,col_gest ),1)
			cv2.putText(menu,"la malla formada",(430,40),cv2.FONT_HERSHEY_SIMPLEX,0.5,(col_gest ,col_gest,col_gest ),1)
			cv2.putText(menu,"por los defectos",(430,60),cv2.FONT_HERSHEY_SIMPLEX,0.5,(col_gest ,col_gest ,col_gest ),1)
			cv2.putText(menu,"de convexidad",(430,80),cv2.FONT_HERSHEY_SIMPLEX,0.5,(col_gest ,col_gest ,col_gest ),1)
			cv2.putText(menu,"en camara",(430,100),cv2.FONT_HERSHEY_SIMPLEX,0.5,(col_gest ,col_gest ,col_gest ),1)
	else:
		cv2.putText(menu,"{}".format(show),(345,80),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,0,255),1)

	# Gestos
	cv2.putText(menu,"G para mostar la deteccion de gestos:",(10,100),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,255,255),1)
	if gests:
		cv2.putText(menu,"{}".format(gests),(330,100),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,0),1)
		if not paint and not fing and not show:
			cv2.putText(menu,"Gestos que reconoce:",(410,20),cv2.FONT_HERSHEY_SIMPLEX,0.5,(col_gest + 50,col_gest + 50,col_gest + 50),1)
			cv2.putText(menu,"Mano cerrada",(430,40),cv2.FONT_HERSHEY_SIMPLEX,0.5,(col_gest,col_gest,col_gest),1)
			cv2.putText(menu,"Mano abierta",(430,60),cv2.FONT_HERSHEY_SIMPLEX,0.5,(col_gest,col_gest,col_gest),1)
			cv2.putText(menu,"Dedos verticalmente",(430,80),cv2.FONT_HERSHEY_SIMPLEX,0.5,(col_gest,col_gest,col_gest),1)
			cv2.putText(menu,"Dedos horizontalmente",(430,100),cv2.FONT_HERSHEY_SIMPLEX,0.5,(col_gest,col_gest,col_gest),1)
	else:
		cv2.putText(menu,"{}".format(gests),(330,100),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,0,255),1)

	# Logo de la aplicacion
	if not paint and not fing and not show and not gests:
		cv2.putText(menu,"HAND",(470,50),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),3)
		cv2.putText(menu,"TRACKER",(440,80),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),3)

	# Retorna el menu
	return np.vstack((frame,menu))