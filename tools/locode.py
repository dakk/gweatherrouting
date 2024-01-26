# export type LocDataRaw = {
# 	Locode: string,
# 	Coordinates: string,
# 	Country: string,
# 	Date: string,
# 	Function: string,
# 	IATA: string,
# 	Location: string,
# 	Name: string,
# 	NameWoDiacritics: string,
# 	Remarks: string,
# 	Status: string,
# 	Subdivision: string
# };

# export type LocData = {
# 	locode: string,
# 	latitude?: number,
# 	longitude?: number,
# 	country: string,
# 	date: Date,
# 	functions: Array<number>,
# 	iata: string,
# 	name: string,
# 	namewod: string,
# 	remarks: string,
# 	status: string,
# 	subdivision: string
# };


# const parseLocData = raw => {
# 	const parseCoordinate = c => {
# 		const min = c.substring(c.length - 3, c.length - 1);
# 		const deg = c.substring(0, c.length - 3);
# 		const sign = c.substring(c.length - 1, c.length);
# 		const lval = (parseInt(deg) + parseInt(min) / 60);

# 		if (sign == 'N' || sign == 'E')
# 			return lval;
# 		else
# 			return -lval;
# 	};

# 	// Coordinates 6130N 00200E
# 	let latitude = null;
# 	let longitude = null;

# 	if (raw.Coordinates != null) {
# 		const coordinates = raw.Coordinates.split(' ');
# 		latitude = parseCoordinate(coordinates[0]);
# 		longitude = parseCoordinate(coordinates[1]);

# 		if (isNaN(latitude) || isNaN(longitude)) {
# 			latitude = longitude = null;
# 		}
# 	}

# 	let functions = [];
# 	if (raw.Function != null)
# 		functions = raw.Function.replace(new RegExp('-', 'g'), '').split('').filter(f => !isNaN(f)).map(f => parseInt(f));

# 	const parsed = {
# 		name: entities.decode(raw.Name),
# 		namewod: entities.decode(raw.NameWoDiacritics),
# 		country: raw.Country,
# 		subdivision: raw.Subdivision,
# 		latitude: latitude,
# 		longitude: longitude,
# 		functions: functions,
# 		locode: raw.Locode,
# 		date: raw.Date,
# 		iata: raw.IATA,
# 		remarks: raw.Remarks,
# 		status: raw.Status
# 	};
# 	return parsed;
# };


# const getLocsData = async (): Promise<Array<LocData>> => {
# 	try {
# 		let results = [];
# 		const res = await request.get("https://www.unece.org/cefact/locode/service/location.html");
# 		const clinksraw = res.split("https://service.unece.org/trade/locode/");

# 		for (let i = 1; i < clinksraw.length; i++) {
# 			const country = clinksraw[i].split('.htm')[0];
# 			let done = false;

# 			while (!done) {
# 				try {
# 					await timeout(1000);
# 					const page = "https://service.unece.org/trade/locode/" + country + ".htm";
# 					const respage = await request.get(page);
# 					const lines = respage.split('<tr>').map(l => l.split('</tr>')[0]);

# 					log.debug('LOCS', `Got page: ${country} (${i}/${clinksraw.length})`);

# 					for (let j = 5; j < lines.length; j++) {
# 						const line = lines[j];
# 						const rows = line.replace(new RegExp('&nbsp;', 'g'), '').split('>').map(l => l.split('<')[0]).filter(l => l.indexOf('\r\n') == -1).map(l => l == '' ? null : l);

# 						results.push({
# 							Locode: rows[1],
# 							Name: rows[2],
# 							NameWoDiacritics: rows[3],
# 							Function: rows[5],
# 							Country: country.toUpperCase().substring(0,2),
# 							Coordinates: rows[9],
# 							Subdivision: rows[4],
# 							Status: rows[6],
# 							Date: rows[7],
# 							IATA: rows[8],
# 							Remarks: rows[10]
# 						});
# 					};
# 					done = true;
# 				} catch (err) {
# 					log.error('UpdatePort', `Error getting page ${country}: ${err}`);
# 				}
# 			}
# 		}

# 		results = results
# 			.map(parseLocData)
# 			.filter(l => l.functions.indexOf(1) != -1)	// Get only locs with port
# 			.filter(l => l.locode != null) // Get only locs with valid
# 			.filter(l => l.latitude != null && l.longitude != null); // Get only valid position ports

# 		return results;
# 	} catch (err) {
# 		return Promise.reject(err);
# 	}
# };


# const updatePortData = async () => {
# 	const updateField = (locdb: $PortDocument, loc: LocData, fname: string) => {
# 		if (typeof (loc[fname]) == 'object' && loc[fname] != null) {
# 			if (loc[fname].length == locdb[fname].length)
# 				return false;
# 		} else if (loc[fname] == locdb[fname])
# 			return false;

# 		log.debug('UpdatePort', `LOCS - ${loc.locode} - updating field ${fname}: ${JSON.stringify(loc[fname])}`);
# 		locdb[fname] = loc[fname];
# 		return true;
# 	};

# 	log.info('UpdatePort', `LOCS - Updating port data`);

# 	try {
# 		let nupdated = 0;
# 		log.debug('UpdatePort', `LOCS - Getting port data...`);
# 		const locsdata = (await getLocsData())
# 		// .filter(l => l.country == 'IT');

# 		log.info('UpdatePort', `LOCS - Got ${locsdata.length} port entries`);

# 		/* Update each port */
# 		for (let j = 0; j < locsdata.length; j++) {
# 			const loc = locsdata[j];
# 			let mod = false;

# 			/* Get existing port */
# 			let port: $PortDocument = await Port.findOne({ locode: loc.locode }).exec();
# 			if (port != null) {

# 			} else {
# 				log.info('UpdatePort', `LOCS - New port found: ${loc.locode}`);
# 				port = new Port();
# 			}

# 			/* Update data */
# 			mod = updateField(port, loc, 'locode') || mod;
# 			mod = updateField(port, loc, 'name') || mod;
# 			mod = updateField(port, loc, 'namewod') || mod;
# 			mod = updateField(port, loc, 'country') || mod;
# 			mod = updateField(port, loc, 'subdivision') || mod;
# 			mod = updateField(port, loc, 'functions') || mod;

# 			if (port.position.coordinates.length == 0 && loc.longitude && loc.latitude) {
# 				port.position = {
# 					type: 'Point',
# 					coordinates: [loc.longitude, loc.latitude]
# 				};
# 				mod = true;
# 				log.debug('UpdatePort', `LOCS - ${loc.locode} - updating field position: ${JSON.stringify(loc.latitude)} ${JSON.stringify(loc.longitude)}`);
# 			}

# 			if (mod) {
# 				nupdated += 1;
# 				await port.save();
# 				log.info('UpdatePort', `LOCS - ${loc.locode} - saved`);
# 			}
# 		}

# 		log.debug('UpdatePort', `LOCS - Updated ${nupdated} ports`);
# 	} catch (err) {
# 		log.error('UpdatePort', `Error getting port data: ${err}`);
# 	}
# };
