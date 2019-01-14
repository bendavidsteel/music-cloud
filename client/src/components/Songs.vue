<template>
  <div class="container">
    <div class="row">
      <div class="col-sm-10">
        <h1>MusicCloud</h1>
        <hr><br><br>
        <alert :message=message v-if="showMessage"></alert>
        <button type="button" class="btn btn-success btn-sm" v-b-modal.song-modal>Add Track</button>
        <br><br>
        <table class="table table-hover">
          <thead>
            <tr>
              <th></th>
              <th scope="col">Track Name</th>
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
                <audio controls
                       v-if="song.playback">
                  <source v-bind:src="song.file" type="audio/mpeg">
                  Your browser does not support the audio element.
                </audio>
              </td>
              <td>
                <button
                        type="button"
                        class="btn btn-success btn-sm"
                        v-if="song.file_provided"
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
             title="Add a new track"
             hide-footer>
      <b-form @submit="onSubmit" @reset="onReset" class="w-100">
      <b-form-group id="form-name-group"
                    label="Track Name:"
                    label-for="form-name-input">
          <b-form-input id="form-name-input"
                        ref="formNameInput"
                        type="text"
                        v-model="addSongForm.name"
                        placeholder="Enter track name">
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
             title="Update Track"
             hide-footer>
      <b-form @submit="onSubmitUpdate" @reset="onResetUpdate" class="w-100">
        <b-form-group id="form-name-edit-group"
                    label="Updated Track Name:"
                    label-for="form-name-edit-input">
          <b-form-input id="form-name-edit-input"
                        ref="formNameEditInput"
                        type="text"
                        v-model="editForm.name"
                        placeholder="Enter track name">
          </b-form-input>
        </b-form-group>
        <b-form-group id="form-artist-edit-group"
                      label="Updated Artist:"
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
             size="lg"
             hide-footer>
      <table class="table table-hover">
          <thead>
            <tr>
              <th></th>
              <th scope="col">Song Name</th>
              <th scope="col">Artist</th>
              <th scope="col">Preview</th>
              <th scope="col">Link</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(song, index) in recommended" :key="index">
              <td>
                <img v-bind:src="song.image_url" alt="" height="100" width="100">
              </td>
              <td>{{ song.name }}</td>
              <td>{{ song.artist }}</td>
              <td>
                <audio controls>
                  <source v-bind:src="song.preview_url" type="audio/mpeg">
                  No audio
                </audio>
              </td>
              <td>
                <a v-bind:href="song.spotify_url">Spotify</a>
              </td>
              <td>
                <button
                        type="button"
                        class="btn btn-primary btn-sm"
                        v-b-modal.add-song-modal
                        @click="onAddSong(song, index)">
                    Add track
                </button>
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
      basePath: 'https://3p44ypj9fe.execute-api.us-east-1.amazonaws.com/dev',
      // basePath: 'http://localhost:5000',
    };
  },
  components: {
    alert: Alert,
  },
  methods: {
    getSongs() {
      const path = `${this.basePath}/songs`;
      axios.get(path)
        .then((res) => {
          this.songs = res.data.songs;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        });
    },
    addSong(payload, file) {
      const path = `${this.basePath}/songs`;
      axios.post(path, payload,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })
        .then((response) => {
          this.uploadSong(response.data.presigned, file);
          this.message = 'Song added!';
          setTimeout(() => { this.message = ' '; }, 1000);
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
          this.getSongs();
        });
    },
    updateSong(payload, songID, file) {
      const path = `${this.basePath}/songs/${songID}`;
      axios.put(path, payload,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })
        .then((response) => {
          this.uploadSong(response.data.presigned, file);
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
      const path = `${this.basePath}/songs/${songID}`;
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
      const path = `${this.basePath}/songs/${song.id}`;
      axios.get(path)
        .then((response) => {
          const link = document.createElement('a');
          link.href = response.data.file_url;
          link.download = response.data.file_name;
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
    uploadSong(presigned, file) {
      if (file) {
        const formData = new FormData();
        formData.append('key', presigned.fields.key);
        formData.append('ACL', presigned.fields.ACL);
        formData.append('Content-Type', presigned.fields['Content-Type']);
        formData.append('signature', presigned.fields.signature);
        formData.append('policy', presigned.fields.policy);
        formData.append('AWSAccessKeyId', presigned.fields.AWSAccessKeyId);
        formData.append('x-amz-security-token', presigned.fields['x-amz-security-token']);
        formData.append('file', file);
        axios.post(presigned.url, formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          })
          .then(() => {
            this.getSongs();
          })
          .catch(() => {
          });
      } else {
        this.getSongs();
      }
    },
    recommendSongs(song) {
      const path = `${this.basePath}/recommend/${song.id}`;
      axios.get(path)
        .then((response) => {
          this.recommended = response.data.songs;
        })
        .catch(() => {
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
      if (this.addSongForm.file) {
        formData.append('file', 'True');
      } else {
        formData.append('file', 'False');
      }
      this.addSong(formData, this.addSongForm.file);
      this.initForm();
    },
    onSubmitUpdate(evt) {
      evt.preventDefault();
      this.$refs.editSongModal.hide();

      const formData = new FormData();

      formData.append('name', this.editForm.name);
      formData.append('artist', this.editForm.artist);
      if (this.editForm.file) {
        formData.append('file', 'True');
      } else {
        formData.append('file', 'False');
      }

      this.updateSong(formData, this.editForm.id, this.editForm.file);
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
    onRecommendSongs(song) {
      this.recommended = [];
      this.recommendSongs(song);
    },
    onAddSong(song) {
      const formData = new FormData();

      formData.append('name', song.name);
      formData.append('artist', song.artist);

      this.addSong(formData, null);
    },
  },
  beforeMount() {
    this.getSongs();
  },
};
</script>
