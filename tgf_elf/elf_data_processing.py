import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

class ELF_Data_Processing_Class(object):
	# P = pi/180
	CONST_P = np.pi/180

	def __init__(self,filename,delta_day,delta_night,time,A,stantion,
				 degree,sigma,plot,datetime,idd,dest_img):
		self.CONST_FS, self.CONST_FN, self.CONST_SCALE, self.CONST_DELTAF, \
		 _, _, _, _ = stantion()
		self.filename = filename
		self.dd = delta_day + 1/self.CONST_DELTAF
		self.dn = delta_night + 1/self.CONST_DELTAF
		self.DEGREE = degree
		self.plot = plot
		self.SIGMA = sigma
		# time in this 5 min in second
		self.time = time
		# A - azimuth, degree
		self.A = A
		self.id = idd
		self.datetime = datetime
		self.CONST_SCALE = self.CONST_SCALE*1e-12
		self.dest_img = dest_img

	def read_data(self):
		self.channel1,self.channel2 = [],[]
		with open(self.filename,'r') as f:
			lines = f.readlines()[1:]
			for s in lines:
				self.channel1.append(int(s[:s.find('\t')]))
				self.channel2.append(int(s[s.find('\t')+1:]))
		return self.channel1,self.channel2,len(self.channel1)

	def channels_to_data(self):
		self.data = [np.sqrt(self.detrended1[i]**2+self.detrended2[i]**2)
					 for i in range(self.N)]
		return self.data

	def filtering(self,data):
		b, a = signal.butter(N=3,Wn=[(50-0.5)/self.CONST_FN,(50+0.5)/self.CONST_FN],
							 btype='bandstop',analog=False)
		filtered1 = signal.lfilter(b, a, data)
		try:
			b, a = signal.butter(N=3,Wn=[(150-0.5)/self.CONST_FN,(150+0.5)/self.CONST_FN],
								 btype='bandstop',analog=False)
			filtered2 = signal.lfilter(b, a, filtered1)

			b, a = signal.butter(N=3,Wn=[(250-0.5)/self.CONST_FN,(250+0.5)/self.CONST_FN],
								 btype='bandstop',analog=False)
			filtered = signal.lfilter(b, a, filtered2)
		except ValueError:
			filtered = filtered1
		# if self.plot:
		# 	self.plot_filtering()

		return list(filtered)

	def plot_filtering(self):
		fig = plt.figure()

		ax1 = fig.add_subplot(2,1,1)
		ax1.semilogy(np.fft.rfftfreq(n=self.N,d=1/self.CONST_FS),
				np.abs(np.fft.rfft(self.data))**2,label='data',color='red')
		ax1.semilogy(np.fft.rfftfreq(n=self.N,d=1/self.CONST_FS),
				np.abs(np.fft.rfft(self.filtered))**2,label='filtered',color='blue')
		ax1.set_title('Spectum '+self.filename)
		ax1.set_xlabel('Freq, Hz')
		ax1.set_ylabel('log(W**2)')
		ax1.grid()
		ax1.legend()

		ax2 = fig.add_subplot(2,1,2)
		ax2.plot(self.t,
				self.data,label='data',color='red')
		ax2.plot(self.t,
				self.filtered,label='filtered',color='blue')
		ax2.set_title('Data '+self.filename)
		ax2.set_xlabel('Time, sec')
		ax2.set_ylabel('Amplitude')
		ax2.grid()
		ax2.legend()

		plt.subplots_adjust(hspace=0.4)
		plt.show()

	def detrending(self,filtered):
		mov_avg = filtered[:self.DEGREE]
		detrended=[0]*self.DEGREE
		for i in range(self.DEGREE,self.N-self.DEGREE):
			chunk = filtered[i-self.DEGREE:i+self.DEGREE+1]
			chunk = sum(chunk)/len(chunk)
			mov_avg.append(chunk)
			detrended.append(filtered[i]-chunk)
		detrended = detrended+[0]*self.DEGREE
		mov_avg = mov_avg+filtered[-self.DEGREE:]
		return detrended,mov_avg

	def peaking(self,detrended):
		peaked = detrended[:]
		# plt.plot(self.t,peaked,label='step 0')

		std0 = np.nanstd(peaked)
		# plt.axhline(std0,c='orange')
		# plt.axhline(-std0,c='orange')

		for i in range(self.N):
			if abs(peaked[i])>self.SIGMA*std0:
				peaked[i] = np.nan #self.SIGMA*std0*np.sign(peaked[i])
		# plt.plot(self.t,eaked,label='step 1')

		std1 = np.nanstd(peaked)
		# plt.axhline(std1,c='red')
		# plt.axhline(-std1,c='red')

		for i in range(self.N):
			if abs(peaked[i])>self.SIGMA*std1:
				peaked[i] = np.nan #self.SIGMA*std1*np.sign(peaked[i])
		# plt.plot(self.t,peaked,label='step 2')

		std2 = np.nanstd(peaked)
		# plt.axhline(std2,c='green')
		# plt.axhline(-std2,c='green')
		for i in range(self.N):
			if abs(peaked[i])>self.SIGMA*std2:
				peaked[i] = np.nan #self.SIGMA*std2*np.sign(peaked[i])
		# plt.plot(self.t,peaked,label='step 3')

		std3 = np.nanstd(peaked)
		# plt.axhline(std3,c='black')
		# plt.axhline(-std3,c='black')

		for i in range(self.N):
			if abs(peaked[i])>self.SIGMA*std3:
				peaked[i] = np.nan #self.SIGMA*std3*np.sign(peaked[i])
		# plt.plot(self.t,peaked,label='step 4')

		# plt.legend()
		# plt.grid()
		# plt.xlabel('Time, sec')
		# plt.ylabel('Amplitude')
		# plt.title('Peaking '+self.filename)
		# if self.plot:
		# 	plt.show()

		return peaked,std2

	def azimuth(self):
		if self.CONST_DELTAF==51.8:
			return [(np.arctan2(-self.detrended1[i],self.detrended2[i])/self.CONST_P+360)%360
					for i in range(self.N)], \
				   [((np.arctan2(-self.detrended1[i],self.detrended2[i])/self.CONST_P+360)%360+180)%360
					for i in range(self.N)]
		else:
			return [(np.arctan2(self.detrended1[i],self.detrended2[i])/self.CONST_P+360)%360
					for i in range(self.N)], \
				   [((np.arctan2(self.detrended1[i],self.detrended2[i])/self.CONST_P+360)%360+180)%360
					for i in range(self.N)]

	def plot_antennas(self):
		fig = plt.figure()
		fig.tight_layout()
		time_array = [ti for ti in self.t if ti>self.time-10e-3 and ti<self.time+210e-3]
		start = self.t.index(time_array[0])
		end = self.t.index(time_array[-1])+1

		ax1 = fig.add_subplot(3,1,1)
		ax1.plot(time_array,[self.channel1[i]-self.mov_avg1[i] for i in range(start,end)],color='yellow',label='data')
		ax1.plot(time_array,self.detrended1[start:end],label='filter',color='red',marker='o',markersize=1.5)
		ax1.axhline(0,color='black')
		ax1.axvline(self.time,color='grey')
		ax1.axvline(self.time+self.dd,color='grey',linestyle=':')
		ax1.axvline(self.time+self.dn,color='grey',linestyle='--')
		ax1.axhline(self.std1,color='lightgreen',linestyle=':')
		ax1.axhline(-self.std1,color='lightgreen',linestyle=':')
		ax1.axhline(2*self.std1,color='lightsalmon',linestyle=':')
		ax1.axhline(-2*self.std1,color='lightsalmon',linestyle=':')
		ax1.axhline(3*self.std1,color='lightskyblue',linestyle=':')
		ax1.axhline(-3*self.std1,color='lightskyblue',linestyle=':')
		ax1.set_ylabel('Antenna NS, pT')
		ax1.set_title('TGF'+self.id+', '+self.datetime+', '+'deg'+str(self.DEGREE)+', sgm'+str(self.SIGMA)+', A='+str(round(self.A)))
		ax1.legend(loc=1)
		ax1.set_xlim([time_array[0],time_array[-1]])

		ax2 = fig.add_subplot(3,1,2,sharex=ax1)
		ax2.plot(time_array,[self.channel2[i]-self.mov_avg2[i] for i in range(start,end)],color='yellow',label='data')
		ax2.plot(time_array,self.detrended2[start:end],label='filter',color='blue',marker='o',markersize=1.5)
		ax2.axhline(0,color='black')
		ax2.axvline(self.time,color='grey')
		ax2.axvline(self.time+self.dd,color='grey',linestyle=':')
		ax2.axvline(self.time+self.dn,color='grey',linestyle='--')
		ax2.axhline(self.std2,color='lightgreen',linestyle=':')
		ax2.axhline(-self.std2,color='lightgreen',linestyle=':')
		ax2.axhline(2*self.std2,color='lightsalmon',linestyle=':')
		ax2.axhline(-2*self.std2,color='lightsalmon',linestyle=':')
		ax2.axhline(3*self.std2,color='lightskyblue',linestyle=':')
		ax2.axhline(-3*self.std2,color='lightskyblue',linestyle=':')
		ax2.set_ylabel('Antenna EW, pT')
		ax2.legend(loc=1)
		ax2.set_xlim([time_array[0],time_array[-1]])

		ax3 = fig.add_subplot(3,1,3,sharex=ax1)
		ax3.plot(time_array,self.total_data[start:end],color='green',label='total data',marker='o',markersize=1.5)
		# ax3.plot(time_array,self.total_peaked[start:end],color='green',label='peaked',marker='o',markersize=1.5)
		ax3.axhline(0,color='black')
		ax3.axvline(self.time,color='grey')
		ax3.axvline(self.time+self.dd,color='grey',linestyle=':')
		ax3.axvline(self.time+self.dn,color='grey',linestyle='--')
		ax3.axhline(self.std_total,color='lightgreen',linestyle=':')
		ax3.axhline(2*self.std_total,color='lightsalmon',linestyle=':')
		ax3.axhline(3*self.std_total,color='lightskyblue',linestyle=':')
		ax3.legend(loc=1)
		ax3.set_xlabel('Time, sec')
		ax3.set_ylabel('Total, pT')
		ax3.set_xlim([time_array[0],time_array[-1]])

		plt.savefig(self.dest_img+'TGF'+str(self.id)+'_'+str(self.datetime)+'data.png',dpi=360)

	def plot_azimuth(self):
		fig = plt.figure()
		fig.tight_layout()
		time_array = [ti for ti in self.t if ti>self.time-20e-3 and ti<self.time+170e-3]
		start = self.t.index(time_array[0])
		end = self.t.index(time_array[-1])+1

		ax1 = fig.add_subplot(3,1,1)
		ax1.plot(time_array,[self.channel1[i]-self.mov_avg1[i] for i in range(start,end)],color='yellow',label='data')
		ax1.plot(time_array,self.peaked1[start:end],label='filter',color='red',marker='o',markersize=1.5)
		ax1.axhline(0,color='black')
		ax1.axvline(self.time,color='grey')
		ax1.axvline(self.time+self.dd,color='grey',linestyle=':')
		ax1.axvline(self.time+self.dn,color='grey',linestyle='--')
		ax1.axhline(self.std1,color='lightgreen',linestyle=':')
		ax1.axhline(-self.std1,color='lightgreen',linestyle=':')
		ax1.axhline(2*self.std1,color='lightsalmon',linestyle=':')
		ax1.axhline(-2*self.std1,color='lightsalmon',linestyle=':')
		ax1.axhline(3*self.std1,color='lightskyblue',linestyle=':')
		ax1.axhline(-3*self.std1,color='lightskyblue',linestyle=':')
		ax1.set_ylabel('Antenna NS')
		ax1.set_title('TGF'+self.id+', '+self.datetime+', '+'deg'+str(self.DEGREE)+', A='+str(round(self.A)))
		ax1.legend(loc=1)
		ax1.set_xlim([time_array[0],time_array[-1]])

		ax2 = fig.add_subplot(3,1,2,sharex=ax1)
		ax2.plot(time_array,[self.channel2[i]-self.mov_avg2[i] for i in range(start,end)],color='yellow',label='data')
		ax2.plot(time_array,self.peaked2[start:end],label='filter',color='blue',marker='o',markersize=1.5)
		ax2.axhline(0,color='black')
		ax2.axvline(self.time,color='grey')
		ax2.axvline(self.time+self.dd,color='grey',linestyle=':')
		ax2.axvline(self.time+self.dn,color='grey',linestyle='--')
		ax2.axhline(self.std2,color='lightgreen',linestyle=':')
		ax2.axhline(-self.std2,color='lightgreen',linestyle=':')
		ax2.axhline(2*self.std2,color='lightsalmon',linestyle=':')
		ax2.axhline(-2*self.std2,color='lightsalmon',linestyle=':')
		ax2.axhline(3*self.std2,color='lightskyblue',linestyle=':')
		ax2.axhline(-3*self.std2,color='lightskyblue',linestyle=':')
		ax2.set_ylabel('Antenna EW')
		ax2.legend(loc=1)
		ax2.set_xlim([time_array[0],time_array[-1]])

		ax3 = fig.add_subplot(3,1,3,sharex=ax1)
		ax3.plot(time_array,self.azimuth_positive[start:end],color='black',label='CG+',marker='o',markersize=1.5)
		ax3.plot(time_array,self.azimuth_negative[start:end],color='violet',label='CG-',marker='o',markersize=1.5)
		ax3.axhline(self.A,label='TGF',color='lime',linewidth=2)
		ax3.axvline(self.time,color='grey')
		ax3.axvline(self.time+self.dd,color='grey',linestyle=':')
		ax3.axvline(self.time+self.dn,color='grey',linestyle='--')
		ax3.legend(loc=1)
		ax3.set_xlabel('Time, sec')
		ax3.set_ylabel('Azimuth, degree')
		ax3.set_xlim([time_array[0],time_array[-1]])

		plt.show()

	def find_peak(self):
		self.azimuth_positive,self.azimuth_negative = self.azimuth()
		# if self.plot:
		# 	self.plot_azimuth()

		print('dd',self.dd)
		print('dn',self.dn)

		peak = max([abs(self.total_data[i]) for i in range(self.N)
					if self.t[i]>=self.time+self.dd-1/self.CONST_FS and
					self.t[i]<=self.time+self.dn+1/self.CONST_FS])
		return peak

	def data_processing(self):
		self.channel1,self.channel2,self.N = self.read_data()
		self.channel1 = [chi/self.CONST_SCALE for chi in self. channel1]
		self.channel2 = [chi/self.CONST_SCALE for chi in self. channel2]

		# t - time array
		self.t = [i*300/self.N for i in range(self.N)]

		# processing for channel1
		self.filtered1 = self.filtering(self.channel1)
		self.detrended1,self.mov_avg1 = self.detrending(self.filtered1)
		# self.detrended1,self.std1 = self.peaked1
		self.peaked1,self.std1 = self.peaking(self.detrended1)
		# if self.plot:
		# 	self.plot_processing()

		# processing for channel2
		self.filtered2 = self.filtering(self.channel2)
		self.detrended2,self.mov_avg2 = self.detrending(self.filtered2)
		# self.detrended2,self.std2 = self.peaked2
		self.peaked2,self.std2 = self.peaking(self.detrended2)
		# if self.plot:
		# 	self.plot_processing()

		# data = sqrt(channel1**2 + channel2**2)
		self.total_data = self.channels_to_data()
		self.total_peaked,self.std_total = self.peaking(self.total_data)
		# self.std_total = np.std(self.total_data)
		if self.plot:
			self.plot_antennas()
			self.plot_processing()
		# self.B = self.find_peak()

		# if self.plot:
		# 	plt.plot(self.t,self.total_data,marker='o',markersize=1)
		# 	plt.axvline(self.time+self.dd,color='grey',linestyle=':',label='delta day')
		# 	plt.axvline(self.time+self.dn,color='grey',linestyle='--',label='delta night')
		# 	plt.axvline(self.time,color='grey',label='TGF time')
		# 	plt.grid()
		# 	plt.legend()
		# 	plt.xlabel('Time, sec')
		# 	plt.ylabel('sqrt(NS**2+EW**2)')
		# 	plt.title('Total data')
		# 	plt.show()

		# return self.B/self.CONST_1CALE

	def plot_processing(self):
		fig = plt.figure()
		fig.tight_layout()
		time_array = [ti for ti in self.t if ti>self.time-10e-3 and ti<self.time+210e-3]
		start = self.t.index(time_array[0])
		end = self.t.index(time_array[-1])+1

		ax1 = fig.add_subplot(2,1,1)
		ax1.plot(time_array,self.channel1[start:end],label='data',color='yellow')
		ax1.plot(time_array,self.filtered1[start:end],label='filtered',color='red')
		ax1.plot(time_array,self.mov_avg1[start:end],label='mov avg',color='black')
		ax1.set_title('TGF'+self.id+', '+self.datetime+', '+'deg'+str(self.DEGREE)+', A='+str(round(self.A)))

		ax1.axvline(self.time+self.dd,color='grey',linestyle=':',label='delta day')
		ax1.axvline(self.time+self.dn,color='grey',linestyle='--',label='delta night')
		ax1.axvline(self.time,color='grey',label='TGF time')
		ax1.legend(loc=1)

		ax2 = fig.add_subplot(2,1,2,sharex=ax1)
		ax2.plot(time_array,self.channel2[start:end],label='data',color='yellow')
		ax2.plot(time_array,self.filtered2[start:end],label='filtered',color='blue')
		ax2.plot(time_array,self.mov_avg2[start:end],label='mov avg',color='black')
		ax2.axvline(self.time+self.dd,color='grey',linestyle=':')
		ax2.axvline(self.time+self.dn,color='grey',linestyle='--')
		ax2.axvline(self.time,color='grey')
		ax2.legend(loc=1)

		plt.savefig(self.dest_img'TGF'+str(self.id)+'_'+str(self.datetime)+'proc.png',dpi=360,textsize=10)

if __name__ == '__main__':
	destination = '/root/ELF_data/'
	filename = '200905101155.dat'
	time = 2*60+15.985

	filename = '200811130740.dat'
	time = 4*60+4.279

	dd = 0.050
	dn = 0.042

	A = 98

	elf_data_processing_class = ELF_Data_Processing_Class(filename=filename,
				delta_day=dd,delta_night=dn,time=time,A=A)
	B = elf_data_processing_class.data_processing()

	print('B =',B)

	elf_data_processing_class.plot()
