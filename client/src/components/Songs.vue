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
              <th scope="col">Song Name</th>
              <th scope="col">Artist</th>
              <th scope="col">Listened?</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(song, index) in songs" :key="index">
              <td>{{ song.name }}</td>
              <td>{{ song.artist }}</td>
              <td>
                <span v-if="song.listened">Yes</span>
                <span v-else>No</span>
              </td>
              <td>
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
                        type="text"
                        v-model="addSongForm.name"
                        required
                        placeholder="Enter song name">
          </b-form-input>
        </b-form-group>
        <b-form-group id="form-artist-group"
                      label="Artist:"
                      label-for="form-artist-input">
            <b-form-input id="form-artist-input"
                          type="text"
                          v-model="addSongForm.artist"
                          required
                          placeholder="Enter artist">
            </b-form-input>
          </b-form-group>
        <b-form-group id="form-listened-group">
          <b-form-checkbox-group v-model="addSongForm.listened" id="form-checks">
            <b-form-checkbox value="true">Listened?</b-form-checkbox>
          </b-form-checkbox-group>
        </b-form-group>
        <b-form-file v-model="addSongForm.file" class="mt-3" plain></b-form-file>
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
                        type="text"
                        v-model="editForm.name"
                        required
                        placeholder="Enter name">
          </b-form-input>
        </b-form-group>
        <b-form-group id="form-artist-edit-group"
                      label="Artist:"
                      label-for="form-artist-edit-input">
            <b-form-input id="form-artist-edit-input"
                          type="text"
                          v-model="editForm.artist"
                          required
                          placeholder="Enter artist">
            </b-form-input>
        </b-form-group>
        <b-form-group id="form-listened-edit-group">
          <b-form-checkbox-group v-model="editForm.listened" id="form-checks">
            <b-form-checkbox value="true">Listened?</b-form-checkbox>
          </b-form-checkbox-group>
        </b-form-group>
        <b-form-file v-model="editForm.file" class="mt-3" plain></b-form-file>
        <br/>
        <b-button type="submit" variant="primary">Update</b-button>
        <b-button type="reset" variant="danger">Cancel</b-button>
      </b-form>
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
      addSongForm: {
        name: '',
        artist: '',
        listened: [],
        file: null,
      },
      editForm: {
        id: '',
        name: '',
        artist: '',
        listened: [],
        file: null,
      },
      message: '',
      showMessage: false,
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
          this.showMessage = true;
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
          this.showMessage = true;
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
          this.showMessage = true;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
          this.getSongs();
        });
    },
    initForm() {
      this.addSongForm.name = '';
      this.addSongForm.artist = '';
      this.addSongForm.listened = [];
      this.addSongForm.file = null;
      this.addSongForm.file.name = '';
      this.editForm.id = '';
      this.editForm.name = '';
      this.editForm.artist = '';
      this.editForm.listened = [];
      this.editForm.file = null;
      this.editForm.file.name = '';
    },
    onSubmit(evt) {
      evt.preventDefault();
      this.$refs.addSongModal.hide();
      // reset form
      this.initForm();

      let listened = false;
      if (this.addSongForm.listened[0]) listened = true;

      const formData = new FormData();

      formData.append('name', this.addSongForm.name);
      formData.append('artist', this.addSongForm.artist);
      formData.append('listened', listened);
      formData.append('file', this.addSongForm.file);

      this.addSong(formData);
    },
    onSubmitUpdate(evt) {
      evt.preventDefault();
      this.$refs.editSongModal.hide();
      let listened = false;
      if (this.editForm.listened[0]) listened = true;

      const formData = new FormData();

      formData.append('name', this.addSongForm.name);
      formData.append('artist', this.addSongForm.artist);
      formData.append('listened', listened);
      formData.append('file', this.addSongForm.file);

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
  },
  created() {
    this.getSongs();
  },
};
</script>
