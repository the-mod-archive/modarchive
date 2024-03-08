import {ChiptuneJsPlayer} from './chiptune3/chiptune3.min.js'

let isLoading = false
let songBuf = false	// for later reuse of buffer, e.g. download

init()
function init() {
	initPlayer()

	oncontextmenu = (ev) => {
		nextSong()
		ev.preventDefault()
	}
}

// init ChiptunePlayer
function initPlayer() {
	window.player = new ChiptuneJsPlayer({repeatCount: -1})

	let song, lastPat, lastRow, lastOrder

	// listen to events
	player.onInitialized(() => {
		let params = new URLSearchParams(window.location.search)
		nextSong( params.get('song_id') )
	})
	player.onEnded((ev) => {
		if(!document.getElementById('autoplay').classList.contains('active')) {
			nextSong()
		}
	})
	player.onMetadata((meta) => {
		player.meta = meta
		document.getElementById('seekbar').max = meta.dur
		setMetadata()

		// tracker things
		song = meta.song
		lastPat = -1
		lastRow = -1
		lastOrder = -1
		tracker.innerHTML = getTrackHTML(meta.song)
		orderList.innerHTML = getOrderList(meta.song)
		doResize()

		// MOD infos
		let html = ['<table>']
		if (meta.title) html.push('<tr><td>Title</td><td>',meta.title,'</td></tr>')
		if (meta.artist) html.push('<tr><td>Artist</td><td>',meta.artist,'</td></tr>')
		if (meta.date) html.push('<tr><td>Date</td><td>',meta.date,'</td></tr>')
		html.push('<tr><td>Type</td><td>',meta.type_long,'</td></tr>')
		if (meta.originaltype_long) html.push('<tr><td>Original Type</td><td>',meta.originaltype_long,'</td></tr>')
		if (meta.tracker) html.push('<tr><td>Tracker</td><td>',meta.tracker,'</td></tr>')
		if (meta.container_long) html.push('<tr><td>Container</td><td>',meta.container_long,'</td></tr>')
		if (meta.message.replace(/\n/g,'').trim().length > 0) html.push('<tr><td style="vertical-align:top">Message</td><td>',meta.message.replace(/\n/g,'<br/>'),'</td></tr>')
		if (meta.message.trim() != meta.song.samples.join('\n').trim() && meta.song.samples.join('\n').trim().length >0) {
			html.push('<tr><td style="vertical-align:top">Samples</td><td>')
			for (let i = 0; i < meta.song.samples.length; i++) {
				if(meta.song.samples[i] != '') html.push(meta.song.samples[i],'<br/>')
			}
			html.push('</td></tr>')
		}
		html.push('</table>')

		myInfo.innerHTML = html.join('')
	})
	player.onProgress((dat) => {
		document.getElementById('seekbar').value = dat.pos

		// tracker things
		if (lastPat == dat.pattern && lastRow == dat.row) return
		// visibility by pattern
		if (lastPat != dat.pattern) {
			if (lastPat != -1)document.getElementById('pattern_'+lastPat).classList.add('hidden')
			document.getElementById('pattern_'+dat.pattern).classList.remove('hidden')
		}
		// active row
		if (lastPat != -1) document.getElementById('pattern_'+lastPat+'_'+lastRow).classList.remove('active')
		document.getElementById('pattern_'+dat.pattern+'_'+dat.row).classList.add('active')
		// better scroll to some rows above
		// only when info is not opened
		if (myInfo.classList.contains('hidden')) {
			let scrollToRow = Math.max(0, dat.row - 5)
			document.getElementById('pattern_'+dat.pattern+'_'+scrollToRow).scrollIntoView()
		}

		// active order
		if (dat.order != lastOrder) {
			if (lastOrder != -1) orderList.getElementsByClassName('orderPos')[lastOrder].classList.remove('active')
			orderList.getElementsByClassName('orderPos')[dat.order].classList.add('active')
		}

		lastPat = dat.pattern
		lastRow = dat.row
		lastOrder = dat.order
	})
	player.onError((err) => {
		nextSong()
	})
}
function doResize() {
	tracker.style.height = window.innerHeight - tracker.offsetTop - 10 +'px'
}
onresize = doResize
function setMetadata() {
	const metadata = player.meta
	if(!metadata) return
	document.getElementById('title').innerHTML = metadata['title']

	var subsongs = player.meta.songs
	document.getElementById('subsongs').style.display = (subsongs.length > 1) ? 'block' : 'none'
	if(subsongs.length > 1) {
		var select = document.getElementById('subsong')
		// remove old
		for (let i = select.options.length-1; i > -1; i--) select.removeChild(select.options[i])
		var elt = document.createElement('option')
		elt.textContent = 'Play all subsongs'
		elt.value = -1
		select.appendChild(elt)
		for(var i = 0; i < subsongs.length; i++) {
			var elt = document.createElement('option')
			elt.textContent = subsongs[i]
			elt.value = i
			select.appendChild(elt)
		}
		select.selectedIndex = 0
		player.selectSubsong(-1)
	}

	document.getElementById('seekbar').value = 0
	updateDuration()

	//document.getElementById('library-version').innerHTML = 'Version: '+ player.meta.libopenmptVersion +' ('+ player.meta.libopenmptBuild +')'
}
function updateDuration() {
	//var sec_num = player.duration()
	var sec_num = player.meta.dur
	var minutes = Math.floor(sec_num / 60)
	var seconds = Math.floor(sec_num % 60)
	if (seconds < 10) {seconds = '0' + seconds }
	document.getElementById('duration').innerHTML = minutes + ':' + seconds
}
function getTrackHTML(dat) {
	const html = []
	const chNum = dat.channels.length
	let i = 0 // for later scrolling show 5 above, 5 below + 1 active row
	//for (let ordIdx = 0; ordIdx < dat.orders.length; ordIdx++) {
		//const patIdx = dat.orders[ordIdx].pat
	for (let patIdx = 0; patIdx < dat.patterns.length; patIdx++) { // todo: make this only for the pats used in orders
		const rowNum = dat.patterns[patIdx].rows.length
		
		let tblCls = 'hidden'
		if (i == dat.orders[0].pat) tblCls = ''
		html.push('<table id="pattern_'+patIdx+'" class="'+tblCls+'">')
		for (let rowIdx = 0; rowIdx < rowNum; rowIdx++) {
			let clsName = ''
			if (i == 0) clsName = 'active'
			//if (i > 10) clsName = 'hidden'	// display 11 rows, 5above 5below
			html.push('<tr id="pattern_'+patIdx+'_'+rowIdx+'" class="'+clsName+'">')
			html.push('<td class="rowIdx">',rowIdx,'</td>')
			for (let chIdx = 0; chIdx < chNum; chIdx++) {
				html.push('<td>')
					html.push( translate(dat.patterns[patIdx].rows[rowIdx][chIdx]) )
				html.push('</td>')
			}
			html.push('</tr>')
			i++
		}
		//html.push('<tr><td colspan="'+chNum+'" id="pattern_'+patIdx+'_'+rowNum+'" class="hidden"><hr/></td></tr>')	// mark end of pattern
		html.push('</table>')	// now each pattern is a tale for more performance
	}
	html.push('</table>')
	return html.join('')

	function translate(arr) {
		let ret = []
		
		const effects = '-0123456789ABCDEFFHEJKLMNOPQRSTUVWXYZ'
		let notePart = '---'
		let instrumentPart = '--'
		if (arr[0] !== 0) {
			const notesPerOct = 'C|C#|D|D#|E|F|F#|G|G#|A|A#|B'.split('|')
			const oct = Math.floor( (arr[0]-1) / 12.0)	// notesPerOct.length
			notePart = notesPerOct[ (arr[0]-1) % 12 ]
			notePart = notePart.padEnd(2,'-')
			notePart += oct

			instrumentPart = arr[1].toString().padStart(2,'0')
			if (arr[0] == 254) notePart = '^^'
			if (arr[0] == 255) notePart = '=='
		}
		ret.push(notePart)
		//ret.push(' ')
		/* like XMPlay just displays notes
		ret.push(instrumentPart)
		ret.push(' ')
		//ret.push(arr[2])	// VOLUMEEFFECT
		//ret.push(arr[4])	// VOLUME
		if (arr[3] != 0) {
			ret.push(effects[arr[3]])
			ret.push(arr[5].toString(16).padStart(2,'0').toUpperCase())	// PARAMETER
		} else {
			ret.push('---')
		}
		*/
		
		return ret.join('')
	}
}
function getOrderList(dat) {
	const html = []
	for (let i = 0; i < dat.orders.length; i++) {
		const cls = (i==0) ? 'orderPos active' : 'orderPos'
		let orderName = dat.orders[i].pat // dat.orders[i].name ? dat.orders[i].name : dat.orders[i].pat
		if (dat.orders[i].pat == 65534) orderName = '+++'	// named! = +++ skip
		if (dat.orders[i].pat == 65535) orderName = '---'	// named! = -- stop
		html.push('<span onclick="player.setOrderRow(',i,',0)" class="',cls,'">',orderName,'</span>')
	}
	return html.join('')
}

window.nextSong = (song_id) => {
	if (isLoading) return

    // TODO: Change this to retrieve the requested song
    song_id = song_id || '26849'
    let url = '/api/v1/download/' + song_id;

	isLoading = true
	fetch(url)
	.then(r => r.arrayBuffer())
    .then(zipArrayBuffer => {
        // Use JSZip to unzip the array buffer
        return JSZip.loadAsync(zipArrayBuffer);
    })
    .then(zip => {
        // Assume there's a single audio file in the zip, you may need to adapt this based on your actual structure
        const audioFile = Object.values(zip.files)[0];

        // Set the filename in the UI
        const filename = audioFile.name.split('/').pop();
        document.getElementById('modfilename').innerText = filename;

        // Extract the audio file as an array buffer
        return audioFile.async('arraybuffer');
    })
	.then(ab => {
		songBuf = ab

		if (player.context.state != 'running') player.context.resume()
		player.play(songBuf)
		isLoading = false
		
		playPause.classList.remove('blink')
		sizeInKB.innerText = (songBuf.byteLength/1024).toFixed(2)

	})
	.catch(e=>console.error(e))
}
window.togglePause = () => {
	// audio policy
	if (player.context.state != 'running') {
		player.context.resume()
		return
	}
	playPause.classList.toggle('blink')
	player.togglePause()
}
window.toggleLoop = () => {
	autoplay.classList.toggle('active')
	player.setRepeatCount( (autoplay.classList.contains('active')) ? -1 : 0)
}
window.toggleInfo = () => {
	btnInfo.classList.toggle('active')
	myInfo.classList.toggle('hidden')
	doResize()
}
window.saveSong = () => {
	if (!songBuf) return
	let blob = new Blob([songBuf], {type: 'application/octet-stream'})
	const a = document.createElement('a')
	a.style.display = 'none'
	a.download = modfilename.innerText
	const url = URL.createObjectURL(blob)
	a.href = url
	a.click()
	a.remove()
	blob = null
	URL.revokeObjectURL(url)
}
window.addFav = () => {
	// todo
}