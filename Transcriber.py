# import sys
import time
import requests

class Transcriber:

	def __init__(self, api_key):
		self.headers = {
			'authorization': api_key,
			'content-type': 'application/json'
		}

	def __upload(self, filename):

		def read_file(filename, chunk_size=5242880):
			with open(filename, 'rb') as _file:
				while True:
					data = _file.read(chunk_size)
					if not data:
						break
					yield data

		response = requests.post(
			'https://api.assemblyai.com/v2/upload',
			headers=self.headers,
			data=read_file(filename)
			)

		return response.json()['upload_url']

	def __transcribe(self, url):
		json = {
			'audio_url': url
		}

		response = requests.post(
			'https://api.assemblyai.com/v2/transcript',
			json=json,
			headers=self.headers
			)

		return response.json()['id']

	def __get_status(self, id):
		endpoint = "https://api.assemblyai.com/v2/transcript/{}".format(id)
		response = requests.get(
			endpoint,
			headers=self.headers
			)
		return response.json()['status']

	def __get_srt(self, id):
		endpoint = "https://api.assemblyai.com/v2/transcript/{}/srt".format(id)
		response = requests.get(
			endpoint,
			headers=self.headers
			)
		return response.content

	def transcribe(self, filename):
		print('Uploading ' + filename)
		file_url = self.__upload(filename)

		print('Sending transcription request from ', file_url)
		transcription_id = self.__transcribe(file_url)

		status = "Sending request"
		while status != 'completed':
			print('Waiting to process file... ({})'.format(status))
			status = self.__get_status(transcription_id)
			time.sleep(3)

		print('Retrieving SRT')
		return self.__get_srt(transcription_id)

# t = Transcriber('e3033b07b0d64a92a73ba97ac5a19a24')
# srt = t.transcribe('sample.mp3')

# print(srt)