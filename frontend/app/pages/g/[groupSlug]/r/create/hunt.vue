<template>
  <div>
    <v-card-title class="headline">
      {{ $t("recipe.hunt-search") }}
    </v-card-title>
    <v-card-text>
      <p>{{ $t("recipe.hunt-search-description") }}</p>
      <v-form @submit.prevent="doSearch(query)">
        <v-text-field
          v-model="query"
          :label="$t('recipe.hunt-search-placeholder')"
          :prepend-inner-icon="$globals.icons.search"
          clearable
          variant="solo-filled"
          rounded
          class="rounded-lg mt-2"
          autofocus
        />
        <div class="d-flex justify-end">
          <v-btn
            type="submit"
            color="primary"
            :loading="loading"
            :disabled="!query"
          >
            {{ $t("general.search") }}
          </v-btn>
        </div>
      </v-form>

      <v-alert
        v-if="error"
        type="error"
        class="mt-4"
      >
        {{ error }}
      </v-alert>

      <v-alert
        v-if="results && results.truncatedToMaxSites"
        type="warning"
        class="mt-4"
      >
        {{ $t("recipe.hunt-truncated-warning") }}
      </v-alert>

      <div v-if="results">
        <v-list v-if="results.results.length > 0">
          <v-list-item
            v-for="result in results.results"
            :key="result.url"
            class="my-2"
          >
            <template #title>
              <span class="font-weight-bold">{{ result.title }}</span>
              <v-chip
                v-if="result.isBlockedSite"
                color="error"
                size="small"
                class="ml-2"
              >
                {{ $t("recipe.hunt-blocked-site-warning") }}
              </v-chip>
            </template>
            <template #subtitle>
              <a
                :href="result.url"
                target="_blank"
                class="text-primary"
              >{{ result.url }}</a>
              <p
                v-if="result.description"
                class="text-body-2 mt-1"
              >
                {{ result.description }}
              </p>
            </template>
            <template #append>
              <v-btn
                variant="tonal"
                color="primary"
                size="small"
                :loading="importingUrl === result.url"
                :disabled="importingUrl !== null && importingUrl !== result.url"
                @click="importOne(result.url)"
              >
                {{ $t("recipe.hunt-import") }}
              </v-btn>
            </template>
          </v-list-item>
        </v-list>

        <p
          v-else
          class="text-center mt-4"
        >
          {{ $t("recipe.hunt-no-results") }}
        </p>

        <div
          v-if="results.results.length > 0"
          class="d-flex justify-center mt-4"
        >
          <v-btn
            variant="outlined"
            :loading="loadingMore"
            @click="loadMore"
          >
            {{ $t("recipe.hunt-load-more") }}
          </v-btn>
        </div>
      </div>
    </v-card-text>
  </div>
</template>

<script setup lang="ts">
import { useUserApi } from "~/composables/api";
import { useNewRecipeOptions } from "~/composables/use-new-recipe-options";
import type { HuntSearchResponse } from "~/lib/api/types/household";

definePageMeta({
  middleware: ["group-only"],
});

const { $globals } = useNuxtApp();
const i18n = useI18n();
const api = useUserApi();
const route = useRoute();

const groupSlug = computed(() => route.params.groupSlug as string);
const query = ref("");
const results = ref<HuntSearchResponse | null>(null);
const loading = ref(false);
const loadingMore = ref(false);
const error = ref<string | null>(null);
const offset = ref(0);
const pageSize = 10;
const importingUrl = ref<string | null>(null);
const { navigateToRecipe } = useNewRecipeOptions();

async function importOne(url: string) {
  if (importingUrl.value) return;
  importingUrl.value = url;
  try {
    const { response } = await api.recipes.createOneByUrl(url, false, false);
    if (response?.status === 201 && response.data) {
      navigateToRecipe(response.data, groupSlug.value, `/g/${groupSlug.value}/r/create/hunt`);
    }
    else {
      error.value = i18n.t("generic.server-error");
    }
  }
  catch {
    error.value = i18n.t("generic.server-error");
  }
  finally {
    importingUrl.value = null;
  }
}

useSeoMeta({
  title: i18n.t("recipe.hunt-search"),
});

async function doSearch(q: string, nextOffset = 0) {
  if (!q) return;
  error.value = null;
  offset.value = nextOffset;
  loading.value = true;
  try {
    const { data } = await api.households.huntSearch({ query: q, count: pageSize, offset: nextOffset });
    results.value = data ?? null;
  }
  catch {
    error.value = i18n.t("generic.server-error");
  }
  finally {
    loading.value = false;
  }
}

async function loadMore() {
  if (!query.value || !results.value) return;
  loadingMore.value = true;
  const nextOffset = offset.value + pageSize;
  try {
    const { data } = await api.households.huntSearch({ query: query.value, count: pageSize, offset: nextOffset });
    if (data) {
      results.value = {
        ...data,
        results: [...results.value.results, ...data.results],
      };
      offset.value = nextOffset;
    }
  }
  finally {
    loadingMore.value = false;
  }
}
</script>
