<template>
  <div>
    <Navbar>
      <slot>
        <div class="ml-auto d-flex align-items-center">
          <SpinKit v-if="isLoading" class="mr-3" />
          <b-form @submit.prevent="queryAnalyses">
            <b-form-input v-model="query" placeholder="search family, status" />
          </b-form>
        </div>
      </slot>
    </Navbar>

    <AnalysisTable :analyses="allAnalyses" />
  </div>
</template>

<script>
  import { mapGetters } from 'vuex'
  import Navbar from '~/components/Navbar'
  import AnalysisTable from '~/components/AnalysisTable'
  import SpinKit from '~/components/SpinKit'

  export default {
    middleware: ['authenticated'],
    data () {
      return {
        query: '',
        isLoading: false
      }
    },
    async fetch ({ store, app }) {
      await store.dispatch('fetchAnalyses', { perPage: 50 })
    },
    computed: {
      ...mapGetters([ 'allAnalyses' ])
    },
    methods: {
      async queryAnalyses () {
        this.isLoading = true
        await this.$store.dispatch('fetchAnalyses', { query: this.query, perPage: 50 })
        this.isLoading = false
      }
    },
    components: {
      AnalysisTable,
      Navbar,
      SpinKit
    }
  }
</script>
