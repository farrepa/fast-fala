# fast-fala

A minimal static-site generator for FALA. Standalone and independent of LAALAA.
Geocodes with postcodes.io and calculates nearest providers with Turf.js 

Demo at https://fast-fala.mapst.ac


## Dev Quickstart

    docker build --tag fast_fala .
    docker run -it -p 8080:80 fast_fala

Edit your /etc/hosts to match server_name in srv/nginx.conf
e.g. 127.0.0.1 fast-fala.mapst.ac

Visit http://fast-fala.mapst.ac:8080

That approach builds the static site into the container for simplicity.

Subsequently build outside the container and run with

    docker run --mount type=bind,source="$(pwd)"/dist,target=/app/dist -it fast_fala python update_website.py
    docker run --mount type=bind,source="$(pwd)"/dist,target=/app/dist -it -p 8080:80 fast_fala
