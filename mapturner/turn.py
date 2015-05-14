#!/usr/bin/env python

import os
import re
import subprocess
import zipfile

import envoy
import requests
import yaml

import utils

class TurnCommand(object):
    def __init__(self):
        self.args = None
        self.config = None

    def __call__(self, args):
        self.args = args

        with open(self.args.config, 'r') as f:
            self.config = yaml.load(f)

        geojson_paths = []

        for name, layer in self.config['layers'].items():
            if 'path' not in layer:
                print 'path missing for layer %s' % name
                return

            local_path = self.get_real_layer_path(layer['path'])

            print 'Processing %s' % name

            if layer['type'] == 'shp':
                geojson_path = self.process_ogr2ogr(name, layer, local_path)
                geojson_paths.append(self.process_topojson(name, layer, geojson_path))
            elif layer['type'] == 'json':
                geojson_paths.append(self.process_topojson(name, layer, local_path))
            elif layer['type'] == 'csv':
                geojson_paths.append(self.process_topojson(name, layer, local_path))
            else:
                raise Exception('Unsupported layer type: %s' % layer['type'])

        self.merge(geojson_paths)

    def add_argparser(self, root, parents):
        """
        Add arguments for this command.
        """
        parser = root.add_parser('turn', parents=parents)
        parser.set_defaults(func=self)

        parser.add_argument(
            dest='config', action='store',
            help='path to YAML configuration file.'
        )

        parser.add_argument(
            dest='output_path', action='store',
            help='path for TopoJSON file.'
        )

        return parser

    def get_real_layer_path(self, path):
        """
        Get the path the actual layer file.
        """
        filename = path.split('/')[-1]
        local_path = path
        filetype = os.path.splitext(filename)[1]

        # Url
        if re.match(r'^[a-zA-Z]+://', path):
            local_path = os.path.join(utils.DATA_DIRECTORY, filename)

            if not os.path.exists(local_path):
                print 'Downloading %s...' % filename
                self.download_file(path, local_path)
        # Non-existant file
        elif not os.path.exists(local_path):
            raise Exception('%s does not exist' % local_path)

        real_path = path

        # Zip files
        if filetype == '.zip':
            slug = os.path.splitext(filename)[0]
            real_path = os.path.join(utils.DATA_DIRECTORY, slug)

            if not os.path.exists(real_path):
                print 'Unzipping...'
                self.unzip_file(local_path, real_path)

        return real_path

    def download_file(self, url, local_path):
        """
        Download a file from a remote host.
        """
        response = requests.get(url, stream=True)

        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()

    def unzip_file(self, zip_path, output_path):
        """
        Unzip a local file into a specified directory.
        """
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(output_path)

    def process_ogr2ogr(self, name, layer, input_path):
        """
        Process a layer using ogr2ogr.
        """
        output_path = os.path.join(utils.DATA_DIRECTORY, '%s.json' % name)

        if os.path.exists(output_path):
            os.remove(output_path)

        ogr2ogr_cmd = [
            'ogr2ogr',
                '-f', 'GeoJSON',
                '-clipsrc', self.config['bbox']
        ]

        if 'where' in layer:
            ogr2ogr_cmd.extend([
                '-where', '"%s"' % layer['where']
            ])

        ogr2ogr_cmd.extend([
            output_path,
            input_path
        ])

        r = envoy.run(' '.join(ogr2ogr_cmd))

        if r.status_code != 0:
            print r.std_err

        return output_path

    def process_topojson(self, name, layer, input_path):
        """
        Process layer using topojson.
        """
        output_path = input_path

        topo_cmd = [
            'topojson',
            '-o', output_path
        ]

        if 'id-property' in layer:
            topo_cmd.extend([
                '--id-property', layer['id-property']
            ])

        if 'properties' in layer:
            topo_cmd.extend([
                '-p', ','.join(layer['properties'])
            ])

        topo_cmd.extend([
            '--',
            input_path
        ])

        s = envoy.run(' '.join(topo_cmd))

        if s.std_err:
            print s.std_err

        return output_path

    def merge(self, paths):
        """
        Merge data layers into a single topojson file.
        """
        r = envoy.run('topojson -o %(output_path)s --bbox -p -- %(paths)s' % {
            'output_path': self.args.output_path,
            'paths': ' '.join(paths)
        })

        if r.status_code != 0:
            print r.std_err
