<template>
  <div>
    <v-form ref="domForm" @submit.prevent="submitBulkText">
      <div>
        <v-card-title class="headline">
          {{ $t("recipe.bulk-text-import-title") }}
        </v-card-title>
        <v-card-text>
          <p>{{ $t("recipe.bulk-text-import-description") }}</p>

          <!-- File upload -->
          <v-file-input
            v-model="uploadedFile"
            accept=".md,.txt"
            :label="$t('general.file')"
            prepend-icon=""
            :prepend-inner-icon="$globals.icons.file"
            variant="solo-filled"
            clearable
            class="rounded-lg mt-4"
            :disabled="state.loading"
            @change="onFileSelected"
          />

          <div class="text-center my-2">
            {{ $t("general.or") }}
          </div>

          <!-- Paste textarea -->
          <v-textarea
            v-model="textContent"
            :label="$t('recipe.bulk-text-import-title')"
            :placeholder="$t('recipe.bulk-text-import-placeholder')"
            variant="solo-filled"
            rows="10"
            class="rounded-lg"
            :disabled="state.loading"
            auto-grow
          />
        </v-card-text>

        <v-card-actions class="justify-center">
          <div style="width: 100%" class="text-center">
            <div style="width: 250px; margin: 0 auto">
              <BaseButton
                :disabled="!textContent"
                rounded
                block
                type="submit"
                :loading="state.loading"
              />
            </div>
            <v-card-text class="py-2">
              {{ progressMessage }}&nbsp;
            </v-card-text>
          </div>
        </v-card-actions>
      </div>
    </v-form>

    <!-- Results -->
    <v-expand-transition>
      <div v-if="recipeResults.length > 0">
        <v-divider class="my-4" />
        <v-card-title>{{ $t("recipe.bulk-text-import-results-title") }}</v-card-title>

        <v-alert
          v-if="summary?.truncated"
          type="warning"
          class="mx-4 mb-4"
        >
          {{ $t("recipe.bulk-text-import-truncated-warning") }}
        </v-alert>

        <v-list lines="one">
          <v-list-item
            v-for="(result, idx) in recipeResults"
            :key="idx"
          >
            <template #prepend>
              <v-icon
                :color="result.status === 'created' ? 'success' : 'error'"
              >
                {{ result.status === "created" ? $globals.icons.check : $globals.icons.close }}
              </v-icon>
            </template>
            <v-list-item-title>
              <a
                v-if="result.status === 'created' && result.recipe_slug"
                :href="`/g/${groupSlug}/r/${result.recipe_slug}`"
                class="text-primary"
              >
                {{ result.recipe_slug }}
              </a>
              <span v-else>{{ $t("recipe.bulk-text-import-recipe-failed") }}</span>
            </v-list-item-title>
            <template #append>
              <v-chip
                :color="result.status === 'created' ? 'success' : 'error'"
                size="small"
                variant="tonal"
              >
                {{
                  result.status === "created"
                    ? $t("recipe.bulk-text-import-recipe-created")
                    : $t("recipe.bulk-text-import-recipe-failed")
                }}
              </v-chip>
            </template>
          </v-list-item>
        </v-list>
      </div>
    </v-expand-transition>

    <!-- Error alert -->
    <v-expand-transition>
      <v-alert
        v-if="state.error"
        color="error"
        class="mt-6"
      >
        {{ $t("new-recipe.error-title") }}
      </v-alert>
    </v-expand-transition>
  </div>
</template>

<script setup lang="ts">
import { useUserApi } from "~/composables/api";
import type { SSEBulkIngestSummary, SSEBulkRecipeDone } from "~/lib/api/types/response";

definePageMeta({
  key: route => route.path,
});

const state = reactive({
  error: false,
  loading: false,
});

const api = useUserApi();
const auth = useMealieAuth();
const route = useRoute();
const groupSlug = computed(() => (route.params.groupSlug as string) || auth.user.value?.groupSlug || "");

const textContent = ref<string>("");
const uploadedFile = ref<File | File[] | null>(null);
const progressMessage = ref<string | null>(null);
const recipeResults = ref<SSEBulkRecipeDone[]>([]);
const summary = ref<SSEBulkIngestSummary | null>(null);

function onFileSelected(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input?.files?.[0];
  if (!file) {
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    textContent.value = (e.target?.result as string) ?? "";
  };
  reader.readAsText(file);
}

async function submitBulkText() {
  if (!textContent.value) {
    return;
  }

  state.loading = true;
  state.error = false;
  recipeResults.value = [];
  summary.value = null;
  progressMessage.value = null;

  try {
    summary.value = await api.recipes.streamBulkTextCreate(
      textContent.value,
      (event: SSEBulkRecipeDone) => {
        recipeResults.value.push(event);
      },
      (message: string) => {
        progressMessage.value = message;
      },
    );
  }
  catch {
    state.error = true;
  }
  finally {
    state.loading = false;
    progressMessage.value = null;
  }
}
</script>
