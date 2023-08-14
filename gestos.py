from funciones import *

# Funcion principal
def main():
	# Leemos el video y comprobamos que se ha leido bien
	cap = cv2.VideoCapture(0)
	if not cap.isOpened:
		print ("Unable to open file")
		exit(0)
	
	# Definimos las variables
	pt1 = (400, 100)
	pt2 = (600, 300)
		
	backSub = cv2.createBackgroundSubtractorMOG2(detectShadows = True)

	paint = fing = show = gests =  False
	paint_list = []
	color = 0

	counter = 0
	cnt_list = []

	type_paint = 1

	# Bucle principal
	while (True):
		# Leemos una imagen y comprobamos que se ha leido bien
		ret,frame=cap.read()
		if not ret:
			exit(0)
		
		# Damos la vuelta a la imagen y guardamos la región de interes
		frame = cv2.flip(frame,1)
		roi = frame[pt1[1]:pt2[1],pt1[0]:pt2[0],:].copy()

		# Aplicamos el filtro de fondo
		gray = cv2.cvtColor(roi,cv2.COLOR_RGB2GRAY)
		ret,bw = cv2.threshold(gray,170,255,cv2.THRESH_BINARY)
		bw = cv2.medianBlur(bw,5)
		fgMask = backSub.apply(bw, None, 0)

		# Buscamos los contornos en la imagen y los pintamos
		contours, _ = cv2.findContours(fgMask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[-2:]
		if show:
			cv2.drawContours(roi, contours, -1, (0,255,0),3)

		# Buscamos el contorno mas grande
		hull, cnt, rect = biggest_contour(contours)

		# Si hay malla, buscamos sus defectos
		if hull is not None:
			fingers = defects(hull, cnt, rect, roi, paint_list, 
							  paint, fing, color, frame, show, type_paint)

			# Comprobamos los gestos
			cnt_list.append(cnt)
			if gests:
				gestos(fingers, cnt_list, frame)
			if counter != 0:
				cnt_list.pop(0)

		# Se incrusta en la imagen la región de interes
		frame[pt1[1]:pt2[1],pt1[0]:pt2[0],:] = roi
		cv2.rectangle(frame,pt1,pt2,(255,0,0))

		# Creamos un menu con las instrucciones
		frame = menu(frame, paint, fing, gests, show)

		# Mostramos la imagen
		cv2.imshow('Frame',frame)

		# Se comprueba si se ha pulsado alguna tecla
		keyboard = cv2.waitKey(1)
		if keyboard & 0xFF == ord('q'):
			break
		elif keyboard & 0xFF == ord('p'):
			paint = not paint
			paint_list = []
		elif keyboard & 0xFF == ord('c'):
			fing = not fing
		elif keyboard & 0xFF == ord('m'):
			show = not show
		elif keyboard & 0xFF == ord('g'):
			gests = not gests
		elif keyboard & 0xFF == ord('1'):
			type_paint = 1
		elif keyboard & 0xFF == ord('2'):
			type_paint = 2
		elif keyboard & 0xFF == ord('3'):
			type_paint = 3
		elif keyboard & 0xFF == ord('4'):
			type_paint = 4

		counter += 1
		color += 1
		if color > 255:
			color = 0

	# Se cierra la ventana
	cap.release()
	cv2.destroyAllWindows()

# Ejecutamos el programa
if __name__ == "__main__":
	main()