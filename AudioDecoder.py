import subprocess

class AudioDecoder:
	def __init__(self, filename):
		self.filename = filename

	# start_time in seconds
	# duration in seconds
	def decode(self, output, start_time, duration):
		start_time = str(start_time)
		duration = str(duration)

		print('Extracting audio from movie.')
		subprocess.call(['ffmpeg', '-i', self.filename, '-ss', start_time, '-t', duration, '-q:a', '0', '-map', '0', output])
		print('Done!')
