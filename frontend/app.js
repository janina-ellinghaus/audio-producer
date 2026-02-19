const { createApp } = Vue;

createApp({
    data() {
        return {
            audioFile: null,
            coverFile: null,
            title: '',
            album: '',
            artist: '',
            year: '',
            track: '',
            genre: '',
            loading: false,
            status: '',
            statusType: ''
        };
    },
    methods: {
        onAudioChange(event) {
            this.audioFile = event.target.files[0];
        },
        onCoverChange(event) {
            this.coverFile = event.target.files[0];
        },
        async convertAudio() {
            if (!this.audioFile || !this.coverFile) {
                this.showStatus('Please select both audio and cover art files', 'error');
                return;
            }

            this.loading = true;
            this.showStatus('Converting audio...', 'loading');

            const formData = new FormData();
            formData.append('audio', this.audioFile);
            formData.append('cover', this.coverFile);
            formData.append('title', this.title);
            formData.append('album', this.album);
            if (this.artist) formData.append('artist', this.artist);
            if (this.year) formData.append('year', this.year);
            if (this.track) formData.append('track', this.track);
            if (this.genre) formData.append('genre', this.genre);

            try {
                const response = await fetch('/api/convert', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Conversion failed');
                }

                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${this.title || 'output'}.mp3`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);

                this.showStatus('✓ Conversion successful! Download started.', 'success');
            } catch (error) {
                this.showStatus(`Error: ${error.message}`, 'error');
            } finally {
                this.loading = false;
            }
        },
        showStatus(message, type) {
            this.status = message;
            this.statusType = type;
        }
    }
}).mount('#app');
