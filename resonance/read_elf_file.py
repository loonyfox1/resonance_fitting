import matplotlib.pyplot as plt

class Read_ELF_File_Class(object):
	def __init__(self,filename,destination):
		self.filename = filename
		self.destination = destination

	def header(self):
		with open(self.destination+self.filename, "rb") as f:
			header = str(f.read(46))
		return header

	def read_bytes(self):
		byte_array = []
		with open(self.destination+self.filename, "rb") as f:
			byte = f.read(1)
			while byte != b'':
				byte_array.append(byte)
				byte = f.read(1)
		return byte_array

	def bytes_to_hex(self):
		byte_array = read_bytes()
		new_byte = []
		for i in range(64,len(byte_array),1):
			time_s = str(byte_array[i])
			time_s = repr(time_s)
			if("\\x" in time_s):
				time_s = time_s[6:8]
			else:
				time_s = hex(ord(time_s[3:4]))[2:]
			new_byte.append(time_s)
		return new_byte

	def hex_to_decimal(self):
		channel1 = []
		channel2 = []
		new_byte = self.bytes_to_hex()
		for i in range(0, len(new_byte), 4):
			time_s1 = new_byte[i] + new_byte[i+1]
			time_s2 = new_byte[i+2] + new_byte[i+3]
			c1 = int(time_s1, 16)
			c2 = int(time_s2, 16)
			channel1.append(c1)
			channel2.append(c2)
		return channel1[:channel1.index(0)],channel2[:channel2.index(0)]

	def read_and_save(self):
		channel1,channel2 = self.hex_to_decimal()
		with open(self.filename, "w") as f:
			for i in range(len(channel1)):
				f.write(repr(channel1[i]),'\t',repr(channel2[i]))
		return self.filename

	def plot(self):
		plt.clf()
		plt.plot(channel1,color='blue',label='NS')
		plt.plot(channel2,color='red',label='EW')
		plt.legend()
		plt.grid()
		plt.ylabel(Amplitude)
		plt.xlabel('Time')
		plt.title(self.header)
		plt.show()

if __name__ == '__main__':
	destination = '/root/ELF_data/'
	filename = '201109062210.dat'

	read_elf_file_class = Read_ELF_File_Class(filename=filename,
											  destination=destination)
	f = read_elf_file_class.read_and_save()
	read_data_from_file.plot()