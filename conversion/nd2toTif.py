#!/usr/bin/env python

def convert(path, startJvm=True, killJvm=True):
	'''
	Provided the path to the directory containing the nd2 files, they will be
	converted to tif format.
	Provided the path to a nd2 file, it will be converted to tif format.
	'''

	import bioformats
	import javabridge
	import numpy
	import os

	if (startJvm):
		javabridge.start_vm(class_path=bioformats.JARS)

	basedir = ''
	tmplist = []

	if (os.path.isdir(path)):
		# Retrieve the file list
		basedir = os.path.join(path, '')
		tmplist = os.listdir(path)
	elif (os.path.exists(path)):
		# Work only on the provided path
		basedir = os.path.dirname(path)
		tmplist.append(os.path.basename(path))

	# Select only nd2 files
	flist = {}
	for fullname in tmplist:
		fname, fext = os.path.splitext(fullname)
		if ('.nd2' == fext):
			flist[fullname] = {'name':fname, 'ext':fext}

	# If no files are provided trigger and error
	if (0 == len(flist)):
		print('\nError: no nd2 files detected')
		return 0

	# Convert each file
	fkeys = flist.keys();
	fkeys.sort();
	for fname in fkeys:
		print('\nWorking on "' + fname)

		# Create output folder
		outdir_base = os.path.join(basedir, flist[fname]['name'], '')
		outdir = outdir_base
		outdir_made = False
		outdir_suffix = 0
		while (not(outdir_made)):
			if (not(os.path.exists(outdir))):
				os.mkdir(outdir)
				print(' Created directory "' + outdir + '".')
				outdir_made = True
			elif (os.path.isdir(outdir)):
				print(' Directory "' + outdir + '" already exists.')
				outdir_made = True
			else:
				outdir_suffix += 1
				outdir = os.path.join(
					outdir_base + '_' + str(outdir_suffix), '')

		# Retrieve metadata
		# Metadata structure at http://goo.gl/63aLUh
		o = bioformats.get_omexml_metadata(os.path.join(basedir, fname))
		o = bioformats.OMEXML(o.encode('ascii', errors = 'ignore'))

		# Retrieve and convert
		with bioformats.ImageReader(os.path.join(basedir, fname)) as reader: 

			# Count series
			series_count = o.image_count
			print(' Found ' + str(series_count) + ' series.')

			# Cycle series
			for series_id in range(series_count):
				print(' Working on series ' + str(series_id + 1))

				# Retrieve shape information
				sizeX = o.image(series_id).Pixels.SizeX
				sizeY = o.image(series_id).Pixels.SizeY
				slice_count = o.image(series_id).Pixels.SizeZ
				channel_count = o.image(series_id).Pixels.channel_count
				print(
					'  Found ' + str(sizeX) + 'x' + str(sizeY) + ' pixels, ' +
					str(slice_count) + ' slices and ' +
					str(channel_count) + ' channels.'
				)

				# Cycle channels
				for channel_id in range(channel_count):
					channel_name = o.image(series_id)
					channel_name = channel_name.Pixels.Channel(channel_id).Name

					outname = channel_name + '.channel' + str(channel_id +1)
					outname += '.series' + str(series_id +1) + '.tif'

					# Check if the channel was previously converted
					if (os.path.exists(os.path.join(outdir, outname))):
						print('  Channel ' + str(channel_id + 1)
							+ ' was previously converted.'
							+ '\n   Remove the file "' + outname
							+ '" to convert it again.')
					else:
						# Read the channel, one slice at a time
						print('  Reading channel ' + str(channel_id + 1)
							+ ' ("' + channel_name + '")')

						image = numpy.zeros(
							(sizeX, sizeY, slice_count), numpy.uint16)

						for slice_id in range(slice_count):
							image[:, :, slice_id] = reader.read(
								t=0,
								z=slice_id,
								c=channel_id,
								series=series_id,
								rescale=False
							)

						p = o.image(0).Pixels
						assert isinstance(p, bioformats.omexml.OMEXML.Pixels)
						p.SizeX = image.shape[1]
						p.SizeY = image.shape[0]
						p.SizeC = 1
						p.SizeT = 1
						p.SizeZ = image.shape[2]
						p.DimensionOrder = bioformats.omexml.DO_XYCZT
						p.PixelType = bioformats.PT_UINT16
						index = image.shape[2]
						
						p.SizeC = image.shape[2]
						p.Channel(0).SamplesPerPixel = image.shape[2]
						o.structured_annotations.add_original_metadata(
							bioformats.omexml.OM_SAMPLES_PER_PIXEL, str(image.shape[2]))

						as_dtype = "<u2"
						buf = numpy.frombuffer(
							numpy.ascontiguousarray(image, as_dtype).data,
							numpy.uint8
						)
						env = javabridge.get_env()
						pixel_buffer = env.make_byte_array(buf)

						xml = o.to_xml()
						script = """
						importClass(Packages.loci.formats.services.OMEXMLService,
									Packages.loci.common.services.ServiceFactory,
									Packages.loci.formats.ImageWriter);
						var service = new ServiceFactory().getInstance(OMEXMLService);
						var metadata = service.createOMEXMLMetadata(xml);
						var writer = new ImageWriter();
						writer.setMetadataRetrieve(metadata);
						writer.setId(path);
						writer.setInterleaved(true);
						writer.saveBytes(index, buffer);
						writer.close();
						"""
						javabridge.run_script(script,
							dict(
								path = os.path.join(outdir, outname),
								xml = xml,
								index = slice_count,
								buffer = pixel_buffer
							)
						)

						# Output in tif format
						# print('  Writing channel ' + str(channel_id + 1)
						# 	+ ' ("' + channel_name + '")')
						# bioformats.write_image(
						# 	os.path.join(outdir, outname),
						# 	image,
						# 	bioformats.PT_UINT16,
						# 	t=0,
						# 	z=slice_id,
						# 	c=0,
						# 	size_t=1,
						# 	size_z=slice_count,
						# 	size_c=1
						# )

	if (killJvm):
		javabridge.kill_vm()

	return 1

# --- #
# RUN #
# --- #

import sys

if (2 > len(sys.argv)):
	msg = 'Please provide the path to the folder'
	msg += 'containing the nd2 files or to the nd2 file itself.'
	sys.exit(msg)
else:
	r = convert(sys.argv[1])
	sys.exit('\nDone!')
