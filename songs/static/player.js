window['libopenmpt'] = {};

function initialize(legacy_id, filename) {
    libopenmpt.onRuntimeInitialized = _ => {
        const player = new ChiptuneJsPlayer(new ChiptuneJsConfig(-1));
        document.querySelector("#play-button").addEventListener("click", play);
        const path = `https://api.modarchive.org/downloads.php?moduleid=${legacy_id}#${filename}`;

        function play() {
            document.getElementById('loading-message').classList.remove('is-hidden');
            player.load(path, afterLoad.bind(this), progress);
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
            document.getElementById('seekbar-section').classList.remove('is-hidden');
            document.getElementById('loading-message').classList.add('is-hidden');
            document.getElementById('play-button-icon').classList.remove('fa-play');
            document.getElementById('play-button-icon').classList.add('fa-pause');
            document.querySelector("#play-button").removeEventListener("click", play);
            document.querySelector("#play-button").addEventListener("click", togglePause);

            document.getElementById('seekbar').addEventListener("change", seek, false);

            player.play(buffer);
            updateDuration();
        }

        function progress(e) {
            if (e.lengthComputable) {
                document.getElementById("loading-message").innerHTML = "Loading... " + Math.floor((e.loaded / e.total) * 100) + "%";
            }
        }

        function updateDuration() {
            const sec_num = player.duration();
            const minutes = Math.floor(sec_num / 60);
            const seconds = Math.floor(sec_num % 60);
            if (seconds < 10) { seconds = '0' + seconds; }
            if (document.getElementById('song-data').classList.contains('is-hidden')) {
                document.getElementById('song-data').classList.remove('is-hidden');
            }
            document.getElementById('song-duration').innerHTML = minutes + ':' + seconds;
            document.getElementById('seekbar').max = sec_num;
        }

        function seek(event) {
            player.seek(event.currentTarget.value);
        }
    };
}