<template>
  <div class="row items-center no-wrap q-gutter-xs tag-scroll">
    <q-btn
      v-for="tag in tags"
      :key="tag"
      dense
      outline
      size="sm"
      color="grey-6"
      :label="tag"
      class="tag-chip"
      @click="$emit('insert', tag)"
    />
  </div>
</template>

<script setup>
defineProps({
  tags: { type: Array, required: true },
})
defineEmits(['insert'])
</script>

<style scoped>
.tag-scroll {
  overflow-x: auto;
  max-width: 100%;
  padding-bottom: 2px;
}
.tag-chip {
  flex: 0 0 auto;
}
</style>
