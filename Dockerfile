FROM grahamdumpleton/mod-wsgi-docker:python-3.4-onbuild
RUN python3 setup.py install
CMD [ "varmed/wsgi.py", "--processes", "2", "--threads", "5" ]
