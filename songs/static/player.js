window['libopenmpt'] = {};

function initialize(legacy_id, filename) {
    libopenmpt.onRuntimeInitialized = _ => {
        const player = new ChiptuneJsPlayer(new ChiptuneJsConfig(-1));
        document.querySelector("#play-button").addEventListener("click", play);
        const path = `https://api.modarchive.org/downloads.php?moduleid=${legacy_id}#${filename}`;

        function play() {
            player.load(path, afterLoad.bind(this, path));
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

        function afterLoad(path, buffer) {
            player.play(buffer);
            document.getElementById('play-button-icon').classList.remove('fa-play');
            document.getElementById('play-button-icon').classList.add('fa-pause');
            document.querySelector("#play-button").removeEventListener("click", play);
            document.querySelector("#play-button").addEventListener("click", togglePause);
        }
    };
}