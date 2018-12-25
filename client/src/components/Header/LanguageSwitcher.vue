<template>
    <b-nav-item-dropdown right :text='`<i class="fas fa-language"></i>`'>
        <b-dropdown-item v-for="(language, key) in $language.available" :key="key" @click="setLanguage(key)">
            {{language}}
        </b-dropdown-item>
    </b-nav-item-dropdown>
</template>

<script lang="ts">
    import Vue from 'vue';
    export default Vue.extend({
        name: '',
        methods: {
            setLanguage (lang: string) {
                this.$language.current = lang;
            }
        }
    });
</script>

<style scoped>

</style>
