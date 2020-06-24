import discord
import asyncio
from discord.ext import commands
from discord.ext.commands import Bot
import praw
import youtube_dl
import boto3
import botocore
from botocore.exceptions import ClientError
import requests

from configparser import ConfigParser

class VideoReuploader(commands.Cog):

	def __init__(self, bot: Bot):
		self.bot = bot
		config = ConfigParser()
		config.read('config.ini')

		CLIENT_ID = config.get('praw', 'reddit_client_id')
		CLIENT_SECRET = config.get('praw', 'reddit_client_secret')
		USER_AGENT = "python:pwpg.bot:v0.0.1 (by u/pwpg_bot)"

		AWS_ACCESS_KEY_ID = config.get('aws', 'access_key_id')
		AWS_SECRET_ACCESS_KEY = config.get('aws', 'secret_access_key')
		self.AWS_BUCKET = config.get('aws', 'bucket_name')
	
		self.reddit = praw.Reddit(client_id = CLIENT_ID,
					 client_secret = CLIENT_SECRET,
					 user_agent = USER_AGENT)

		aws_config = botocore.config.Config(signature_version = botocore.UNSIGNED)
		self.aws_client = boto3.client('s3',
							#config = aws_config,
							aws_access_key_id = AWS_ACCESS_KEY_ID,
							aws_secret_access_key = AWS_SECRET_ACCESS_KEY)

	@commands.command(name='check',
						description = 'Check aws for object name',
						pass_context = True)
	async def check_aws(self, context, target_url):
		try:
			print('waiting for grab_vreddit')
			await asyncio.gather(self.grab_vreddit(target_url))
		#url = self.grab_vreddit(self.get_submission_object(target_url))
		except Exception as e:
			print('timed out')
			print(e)
		#context.send(url)

	async def grab_vreddit(self, target_url):
		# Grabs the title from the reddit submission
		# Determines extension when downloaded with ydl
		submission = self.get_submission_object(target_url)
		title_pattern = f'{submission.title} - {submission.name}'
		heirarchy = f'videos/'
		ydl_opts = {'prefer_ffmpeg' : True,
			'outtmpl' : f'{heirarchy}{title_pattern}.%(ext)s'}

		ydl = youtube_dl.YoutubeDL(ydl_opts)

		print('Finding filename')
		info_dict = ydl.extract_info(submission.url, False)
		filename = f'{ydl.prepare_filename(info_dict)}'
		aws_file_path = f'{heirarchy}{title_pattern}.{info_dict["ext"]}'
		print(f'Filename - {filename}')
		print(aws_file_path)

		url = self.aws_locate(aws_file_path)

		if url is None:
			# needs to be uploaded
			print('No file found on AWS, downloading now')
			ydl.download([submission.url])
			print('Uploading to AWS')
			self.aws_upload(filename, aws_file_path)
		else:
			# package and return the url
			return url

	def aws_upload(self, local_file_path, aws_target_path):
		try:
			self.aws_client.upload_file(local_file_path, self.AWS_BUCKET, aws_target_path,
										ExtraArgs={'ContentType' : 'video/mp4',
													'ACL': 'public-read'})
		except Exception as e:
			print('Upload failed')
			print(e)
			pass
		pass

	def aws_locate(self, file_path):
		try:
			aws_object = self.aws_client.get_object(Bucket = self.AWS_BUCKET,
										Key = f'{file_path}')

			url = self.aws_client.generate_presigned_url('get_object',
												Params = {'Bucket' : self.AWS_BUCKET,
															'Key' : file_path},
												ExpiresIn = 86400)
			
			return self.clean_aws_url(url)
		except ClientError as e:
			return None
		pass

	def get_submission_object(self, target_url):
		# todo change to aiohttp instead of requests
		full_url = requests.head(target_url, allow_redirects = True)
		submission = self.reddit.submission(url = full_url.url)

		return submission

	def clean_aws_url(self, aws_file_path):
		result = aws_file_path.partition("?AWSAccessKeyId=")
		return result[0]


def setup(bot):
	bot.add_cog(VideoReuploader(bot))

def teardown(bot):
	bot.remove_cog('VideoReuploader')