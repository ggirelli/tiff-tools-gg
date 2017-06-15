importClass(Packages.ij.IJ);
importClass(Packages.ij.Menus);
importClass(Packages.ij.gui.GenericDialog);
importClass(Packages.java.io.File);
importClass(Packages.ij.io.FileSaver);
importClass(Packages.ij.io.OpenDialog);
importClass(Packages.loci.plugins.BF);
importClass(Packages['loci.plugins.in.ImporterOptions']);

importClass(Packages.loci.formats.ChannelSeparator);
importClass(Packages.loci.formats.FormatException);
importClass(Packages.loci.formats.IFormatReader);
importClass(Packages.loci.plugins.util.ImageProcessorReader);
importClass(Packages.loci.plugins.util.LociPrefs);

importClass(Packages.java.awt.event.TextListener);
importClass(Packages.java.awt.Color)

// Get folder
od = new OpenDialog("Select folder...");
base_url = od.getDirectory();
folder = new File(base_url);
listOfFiles = folder.listFiles();

// Get extension
ext = od.getPath().split('.');
ext = ext[ext.length - 1];
IJ.log('Working on extension "' + ext + '"');

// Get chnames
var commands = Menus.getCommands();
var keys = commands.keySet();
var gd = new GenericDialog("Channels");
gd.addStringField("Comma-separated channel names in proper order:\n", "dapi,tmr", 20);
var prom = gd.getStringFields().get(0);
prom.setForeground(Color.red);
prom.addTextListener(new TextListener( {
    textValueChanged: function(evt) {
        if (keys.contains(prom.getText()))
            prom.setForeground(Color.black);
        else
            prom.setForeground(Color.red);
    }
}));
gd.showDialog();

// Run conversion
if (!gd.wasCanceled()) {
    var chnames = gd.getNextString().split(',');

	// Get filename notation
	var commands = Menus.getCommands();
	var keys = commands.keySet();
	var gd = new GenericDialog("File-name notation");
	var notations = ['DOTTER notation: e.g., dapi_001', 'GPSeq notation: e.g., dapi.channel001.series001'];
	gd.addRadioButtonGroup('', notations, 2, 1, notations[0]);
	gd.showDialog();

	if (!gd.wasCanceled()) {

		var sel_notation = gd.getNextRadioButton();
		IJ.log('Selected notation. ' + sel_notation);

		IJ.log('Channel names: ' + chnames);

		function pad(num, size) {
			var s = "000000000" + num;
			return s.substr(s.length-size);
		}

		var r = new ImageProcessorReader(
		  new ChannelSeparator(LociPrefs.makeImageReader()));

		for (var i = 0; i < listOfFiles.length; i++) {
			if (listOfFiles[i].isFile()) {

				// Set file
				var name = listOfFiles[i].getName();
				var id = base_url + name;

				// Check matching extension
				if ( name.length <= ext.length ) {
					IJ.log('Skipping file "' + name + '"')
				} else {
					if ( name.substr(name.length - ext.length, name.length) != ext ) {
						IJ.log('Skipping file "' + name + '"')
					} else {

						// Convert
						IJ.showStatus("Examining file " + name);
						IJ.log("Examining file " + name);
						r.setId(id);

						// Count series
						var nseries = r.getSeriesCount();
						IJ.showStatus("Found " + nseries + " FoVs.");
						IJ.log("Found " + nseries + " FoVs.");

						// If there are series
						if ( 0 != nseries ) {

							// Make outdir
							var outdir = base_url + name.split('.')[0] + '/';
							var tmp = new File(outdir).mkdir();

							// Save each series
							for (var sidx = 0; sidx < nseries; sidx++) {
								r.setSeries(sidx);

								nchannels = r.getSizeC();
								IJ.showStatus('Found ' + nchannels + ' channels.');
								IJ.log('Found ' + nchannels + ' channels.');

								var options = new ImporterOptions(); 
								options.setId(id);
								options.setAutoscale(true);
								options.setSplitChannels(true);
								options.setSeriesOn(sidx, true);
								var imps = BF.openImagePlus(options);

								for (var cidx = 0; cidx < nchannels; cidx++) {
									var chname = chnames[cidx].trim();

									if ( sel_notation == notations[0]) {
										IJ.log('Saving to: ' + outdir + chname + '_' + pad(sidx + 1, 3) + '.tif')
										new FileSaver(imps[cidx]).saveAsTiff(outdir + chname + '_' + pad(sidx + 1, 3) + '.tif');
									} else if ( sel_notation == notations[1] ) {
										IJ.log('Saving to: ' + outdir + chname + '.channel' + pad(cidx + 1, 2) + '.series' + pad(sidx + 1, 3) + '.tif')
										new FileSaver(imps[cidx]).saveAsTiff(outdir + chname + '.channel' + pad(cidx + 1, 2) + '.series' + pad(sidx + 1, 3) + '.tif');
									}
								}

							}
							
						}
					}
				}
			}
		}
	}
}

IJ.log('DONE')
