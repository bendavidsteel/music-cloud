<template>
  <div class="container">
    <div class="row">
      <div class="col-sm-10">
        <h1>Songs</h1>
        <hr><br><br>
        <alert :message=message v-if="showMessage"></alert>
        <button type="button" class="btn btn-success btn-sm" v-b-modal.song-modal>Add Song</button>
        <br><br>
        <table class="table table-hover">
          <thead>
            <tr>
              <th></th>
              <th scope="col">Song Name</th>
              <th scope="col">Artist</th>
              <th></th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(song, index) in songs" :key="index">
              <td>
                <img v-bind:src="song.image_url" alt="" height="150" width="150">
              </td>
              <td>{{ song.name }}</td>
              <td>{{ song.artist }}</td>
              <td>
                <audio controls>
                  <source v-bind:src="song.file" type="audio/mpeg">
                  Your browser does not support the audio element.
                </audio>
              </td>
              <td>
                <button
                        type="button"
                        class="btn btn-success btn-sm"
                        v-b-modal.song-download-modal
                        @click="onDownloadSong(song)">
                    Download
                </button>
                <button
                        type="button"
                        class="btn btn-warning btn-sm"
                        v-b-modal.song-update-modal
                        @click="editSong(song)">
                    Update
                </button>
                <button
                        type="button"
                        class="btn btn-danger btn-sm"
                        @click="onDeleteSong(song)">
                    Delete
                </button>
                <button
                        type="button"
                        class="btn btn-primary btn-sm"
                        v-if="song.spotify_found"
                        v-b-modal.recommend-songs-modal
                        @click="onRecommendSongs(song)">
                    Recommend
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <b-modal ref="addSongModal"
             id="song-modal"
             title="Add a new song"
             hide-footer>
      <b-form @submit="onSubmit" @reset="onReset" class="w-100">
      <b-form-group id="form-name-group"
                    label="Song Name:"
                    label-for="form-name-input">
          <b-form-input id="form-name-input"
                        ref="formNameInput"
                        type="text"
                        v-model="addSongForm.name"
                        placeholder="Enter song name">
          </b-form-input>
        </b-form-group>
        <b-form-group id="form-artist-group"
                      label="Artist:"
                      label-for="form-artist-input">
            <b-form-input id="form-artist-input"
                          ref="formArtistInput"
                          type="text"
                          v-model="addSongForm.artist"
                          placeholder="Enter artist">
            </b-form-input>
          </b-form-group>
        <b-form-group id="form-file-group">
          <b-form-file v-model="addSongForm.file"
                       ref="formFileInput"
                       class="mt-3"
                       plain>
          </b-form-file>
        </b-form-group>
        <br/>
        <b-button type="submit" variant="primary">Submit</b-button>
        <b-button type="reset" variant="danger">Reset</b-button>
      </b-form>
    </b-modal>
    <b-modal ref="editSongModal"
             id="song-update-modal"
             title="Update"
             hide-footer>
      <b-form @submit="onSubmitUpdate" @reset="onResetUpdate" class="w-100">
        <b-form-group id="form-name-edit-group"
                    label="Song Name:"
                    label-for="form-name-edit-input">
          <b-form-input id="form-name-edit-input"
                        ref="formNameEditInput"
                        type="text"
                        v-model="editForm.name"
                        placeholder="Enter name">
          </b-form-input>
        </b-form-group>
        <b-form-group id="form-artist-edit-group"
                      label="Artist:"
                      label-for="form-artist-edit-input">
            <b-form-input id="form-artist-edit-input"
                          ref="formArtistEditInput"
                          type="text"
                          v-model="editForm.artist"
                          placeholder="Enter artist">
            </b-form-input>
        </b-form-group>
        <b-form-group id="form-file-edit-group">
          <b-form-file ref="formFileEditInput"
                       v-model="editForm.file"
                       class="mt-3"
                       plain>
          </b-form-file>
        </b-form-group>
        <br/>
        <b-button type="submit" variant="primary">Update</b-button>
        <b-button type="reset" variant="danger">Cancel</b-button>
      </b-form>
    </b-modal>
    <b-modal ref="recommendSongsModal"
             id="recommend-songs-modal"
             title="Recommended"
             hide-footer>
      <table class="table table-hover">
          <thead>
            <tr>
              <th></th>
              <th scope="col">Song Name</th>
              <th scope="col">Artist</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(song, index) in recommended" :key="index">
              <td>
                <img v-bind:src="song.image_url" alt="" height="150" width="150">
              </td>
              <td>{{ song.name }}</td>
              <td>{{ song.artist }}</td>
              <td>
                <audio controls>
                  <source v-bind:src="song.file" type="audio/mpeg">
                  Your browser does not support the audio element.
                </audio>
              </td>
            </tr>
          </tbody>
        </table>
    </b-modal>
  </div>
</template>

<script>
import axios from 'axios';
import Alert from './Alert';

export default {
  data() {
    return {
      songs: [],
      recommended: [],
      addSongForm: {
        name: '',
        artist: '',
        file: null,
      },
      editForm: {
        id: '',
        name: '',
        artist: '',
        file: null,
      },
      message: '',
      showMessage: true,
      basePath: 'http://localhost:5000',
    };
  },
  components: {
    alert: Alert,
  },
  methods: {
    getSongs() {
      const path = 'http://localhost:5000/songs';
      axios.get(path)
        .then((res) => {
          this.songs = res.data.songs;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        });
    },
    addSong(payload) {
      const path = 'http://localhost:5000/songs';
      axios.post(path, payload,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })
        .then(() => {
          this.getSongs();
          this.message = 'Song added!';
          setTimeout(() => { this.message = ' '; }, 1000);
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
          this.getSongs();
        });
    },
    updateSong(payload, songID) {
      const path = `http://localhost:5000/songs/${songID}`;
      axios.put(path, payload,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })
        .then(() => {
          this.getSongs();
          this.message = 'Song updated!';
          setTimeout(() => { this.message = ' '; }, 1000);
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
          this.getSongs();
        });
    },
    removeSong(songID) {
      const path = `http://localhost:5000/songs/${songID}`;
      axios.delete(path)
        .then(() => {
          this.getSongs();
          this.message = 'Song removed!';
          setTimeout(() => { this.message = ' '; }, 1000);
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
          this.getSongs();
        });
    },
    downloadSong(song) {
      const path = `http://localhost:5000/songs/${song.id}`;
      axios.get(path)
        .then((response) => {
          const link = document.createElement('a');
          link.href = response.data.file_url;
          const title = `${song.name}_${song.artist}.mp3`;
          link.setAttribute('download', title); // or any other extension
          document.body.appendChild(link);
          link.click();
          this.message = 'Song downloaded!';
          setTimeout(() => { this.message = ' '; }, 1000);
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        });
    },
    recommendSong(song) {
      const path = `http://localhost:5000/recommend/${song.id}`;
      axios.get(path)
        .then((response) => {
          this.recommended = response.data.recommended;
        })
        .catch((error) => {
          console.error(error);
        });
    },
    initForm() {
      this.addSongForm.name = '';
      this.addSongForm.artist = '';
      this.editForm.id = '';
      this.editForm.name = '';
      this.editForm.artist = '';

      this.$refs.formFileInput.reset();
      this.$refs.formFileEditInput.reset();
    },
    onSubmit(evt) {
      evt.preventDefault();
      this.$refs.addSongModal.hide();

      const formData = new FormData();

      formData.append('name', this.addSongForm.name);
      formData.append('artist', this.addSongForm.artist);
      formData.append('file', this.addSongForm.file);

      this.addSong(formData);
      this.initForm();
    },
    onSubmitUpdate(evt) {
      evt.preventDefault();
      this.$refs.editSongModal.hide();

      const formData = new FormData();

      formData.append('name', this.editForm.name);
      formData.append('artist', this.editForm.artist);
      formData.append('file', this.editForm.file);

      this.updateSong(formData, this.editForm.id);
      this.initForm();
    },
    onReset(evt) {
      evt.preventDefault();
      this.$refs.addSongModal.hide();
      this.initForm();
    },
    onResetUpdate(evt) {
      evt.preventDefault();
      this.$refs.editSongModal.hide();
      this.initForm();
      this.getSongs(); // why?
    },
    onDeleteSong(song) {
      this.removeSong(song.id);
    },
    editSong(song) {
      this.editForm = song;
    },
    onDownloadSong(song) {
      this.downloadSong(song);
    },
    onRecommendSong(song) {
      this.recommendSong(song);
    },
  },
  beforeMount() {
    this.getSongs();
  },
};
</script>
