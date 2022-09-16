window['libopenmpt'] = {};

function initialize(legacy_id, filename) {
    libopenmpt.onRuntimeInitialized = _ => {
        const player = new ChiptuneJsPlayer(new ChiptuneJsConfig(-1));
        const path = `https://api.modarchive.org/downloads.php?moduleid=${legacy_id}#${filename}`;

        if (player.isAudioContextSuspended()) {
            document.querySelector("#play-button").addEventListener("click", downloadAndPlay);
        } else {
            downloadAndPlay();
        }

        function downloadAndPlay() {
            document.getElementById('loading-message').classList.remove('visually-hidden');
            document.querySelector("#play-button").removeEventListener("click", downloadAndPlay);
            player.load(path, afterLoad.bind(this), loadProgress);
        }

        function togglePause() {
            player.togglePause();
            if (document.getElementById('play-button-icon').classList.contains('fa-play')) {
                document.getElementById('play-button-icon').classList.remove('fa-play');
                document.getElementById('play-button-icon').classList.add('fa-pause');
            } else {
                document.getElementById('play-button-icon').classList.add('fa-play');
                document.getElementById('play-button-icon').classList.remove('fa-pause');
            }
        }

        function afterLoad(buffer) {
            document.getElementById('seekbar-section').classList.remove('visually-hidden');
            document.getElementById('loading-message').classList.add('visually-hidden');
            document.getElementById('play-button-icon').classList.remove('fa-play');
            document.getElementById('play-button-icon').classList.add('fa-pause');
            document.querySelector("#play-button").addEventListener("click", togglePause);

            document.getElementById('seekbar').addEventListener("change", seek, false);

            player.play(buffer);
            setInterval(songProgress, 500);

            const subsongs = player.subsongs();
            if (subsongs.length > 1) {
                document.getElementById('subsong-section').classList.remove('visually-hidden');
                const selector = document.getElementById('subsong-selector');

                const elt = document.createElement('option');
                elt.textContent = 'Play all subsongs';
                elt.value = -1;
                selector.appendChild(elt);

                for (let i = 0; i < subsongs.length; i++) {
                    const newOption = document.createElement('option');
                    newOption.textContent = subsongs[i];
                    newOption.value = i
                    selector.appendChild(newOption);
                }

                selector.selectedIndex = 0;
                player.selectSubsong(-1);
                selector.addEventListener("change", selectSubsong, false);
            }

            updateDuration();
        }

        function loadProgress(e) {
            if (e.lengthComputable) {
                document.getElementById("loading-message").innerHTML = "Loading... " + Math.floor((e.loaded / e.total) * 100) + "%";
            }
        }

        function updateDuration() {
            const sec_num = player.duration();
            const minutes = Math.floor(sec_num / 60);
            let seconds = Math.floor(sec_num % 60);
            if (seconds < 10) { seconds = '0' + seconds; }
            if (document.getElementById('song-data').classList.contains('visually-hidden')) {
                document.getElementById('song-data').classList.remove('visually-hidden');
            }
            document.getElementById('song-duration').innerHTML = minutes + ':' + seconds;
            document.getElementById('seekbar').max = sec_num;
        }

        function seek(event) {
            player.seek(event.currentTarget.value);
        }

        function songProgress() {
            document.getElementById('seekbar').value = player.getPosition();
        }

        function selectSubsong(event) {
            player.selectSubsong(event.currentTarget.value);
            updateDuration();
        }
    };
}