import environ


env = environ.Env()
environ.Env.read_env()
KEY=env('KEY')
DEBUG = env.bool('DEBUG', default=False)