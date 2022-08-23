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
            player.play(buffer);
            document.getElementById('loading-message').classList.add('is-hidden');
            document.getElementById('play-button-icon').classList.remove('fa-play');
            document.getElementById('play-button-icon').classList.add('fa-pause');
            document.querySelector("#play-button").removeEventListener("click", play);
            document.querySelector("#play-button").addEventListener("click", togglePause);
        }

        function progress(e) {
            if (e.lengthComputable) {
                document.getElementById("loading-message").innerHTML = "Loading... " + Math.floor((e.loaded / e.total) * 100) + "%";
            }
        }
    };
}