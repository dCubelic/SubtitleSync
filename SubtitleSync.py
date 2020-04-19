import math
import os
import pysrt
import re
import argparse
from AudioDecoder import AudioDecoder
from collections import Counter
from Transcriber import Transcriber

class SubtitleSyncer:
	START_OFFSET = 15
	SHIFT_OFFSET_MILLIS = 400

	def __init__(self, subtitle_name, video_name):
		self.subtitle_name = subtitle_name
		self.video_name = video_name
		self.decoder = AudioDecoder(video_name)
		self.transcriber = Transcriber('69e9fe5fdf7a4600b18781a15e7b9194')

	def __get_cosine(self, str1, str2):
		def text_to_vector(text):
		    words = re.compile(r"\w+").findall(text)
		    return Counter(words)

		vec1 = text_to_vector(str1)
		vec2 = text_to_vector(str2)

		intersection = set(vec1.keys()) & set(vec2.keys())
		numerator = sum([vec1[x] * vec2[x] for x in intersection])

		sum1 = sum([vec1[x] ** 2 for x in list(vec1.keys())])
		sum2 = sum([vec2[x] ** 2 for x in list(vec2.keys())])
		denominator = math.sqrt(sum1) * math.sqrt(sum2)

		if not denominator:
		    return 0.0
		else:
		    return float(numerator) / denominator

	def __srt_time_to_seconds(self, srt):
		return srt.hours * 3600 + \
			srt.minutes * 60 + \
			srt.seconds + \
			srt.milliseconds / 1000

	# TODO
	def __characteristic_srt_time(self, srt):
		start = self.__srt_time_to_seconds(srt[3].start)
		end = self.__srt_time_to_seconds(srt[3].end)
		return start, end-start

	def sync(self):
		srt = pysrt.open(self.subtitle_name)

		srt_start, srt_duration = self.__characteristic_srt_time(srt)
		audio_file = self.video_name[:-3] + 'audio.temp.mp3'

		# Get audio
		self.decoder.decode(audio_file, srt_start - self.START_OFFSET, srt_duration + self.START_OFFSET*2)

		# Get audio transcription
		transcribed_file = self.video_name[:-3] + 'transcribed.srt'
		with open(transcribed_file, 'w') as output:
			transcribed_srt = self.transcriber.transcribe(audio_file).decode('utf8')
			output.write(transcribed_srt)

		transcribed_srt = pysrt.open(transcribed_file)
		transcribed_srt.shift(seconds=srt_start - self.START_OFFSET)
		srt_part = srt.slice(
			starts_after={'hours': (srt_start - self.START_OFFSET)//3600, 'minutes': (srt_start - self.START_OFFSET)//60, 'seconds': (srt_start - self.START_OFFSET)%60},
			ends_before={'hours': (srt_start + srt_duration + self.START_OFFSET)//3600, 'minutes': (srt_start + srt_duration + self.START_OFFSET)//60, 'seconds': (srt_start + srt_duration + self.START_OFFSET)%60}
		)

		# Find most similar subs
		max_similarity = 0
		for srt1 in transcribed_srt:
			for srt2 in srt_part:
				cosine = self.__get_cosine(srt1.text, srt2.text)
				if cosine > max_similarity:
					max_similarity = cosine
					max_srt1 = srt1
					max_srt2 = srt2

		# Perform time shift
		shift = self.__srt_time_to_seconds(max_srt1.start) - self.__srt_time_to_seconds(max_srt2.start)
		srt.shift(seconds=shift, milliseconds=shift%1 - self.SHIFT_OFFSET_MILLIS)
		srt.save(self.subtitle_name[:-3] + 'shifted.srt', encoding='utf-8')
		print("Subtitles shifted for", shift)

		# Cleanup
		os.remove(audio_file)
		os.remove(transcribed_file)


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("-s", "--subtitles", help="Subtitle input file", action="store", type=str)
	parser.add_argument("-v", "--video", help="Video input file", action="store", type=str)
	args = parser.parse_args()

	syncer = SubtitleSyncer(args.subtitles, args.video)
	syncer.sync()

if __name__ == "__main__":
	main()
