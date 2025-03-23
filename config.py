import environ


env = environ.Env()
environ.Env.read_env()
KEY=env('KEY')
MODEL=env('MODEL')
DEBUG = env.bool('DEBUG', default=False)