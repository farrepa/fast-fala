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


## Known issues

- Public datasource does not contain provider websites or organization type
- Organization type filter unimplemented, with no data to filter on
- Provider details in list view not yet implemented
- Missing progress indicator on search
- Missing "No results found" notice


## Unimplemented

- `/terminated_postcodes` lookup on 404s, notification, and outcode logging to highlight service gaps
- Retained pagination behaviour
