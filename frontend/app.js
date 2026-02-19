const { createApp } = Vue;

createApp({
    data() {
        return {
            audioFile: null,
            topic: '',
            speaker: '',
            loading: false,
            status: '',
            statusType: ''
        };
    },
    methods: {
        onAudioChange(event) {
            this.audioFile = event.target.files[0];
        },
        async convertAudio() {
            if (!this.audioFile) {
                this.showStatus('Please select an audio file', 'error');
                return;
            }

            this.loading = true;
            this.showStatus('Converting audio...', 'loading');

            const formData = new FormData();
            formData.append('audioFile', this.audioFile);
            formData.append('topic', this.topic);
            if (this.speaker) formData.append('speaker', this.speaker);

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
