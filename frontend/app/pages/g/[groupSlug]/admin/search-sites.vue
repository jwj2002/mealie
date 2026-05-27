<template>
  <v-container>
    <BasePageTitle divider>
      <template #title>
        {{ $t("admin.search-sites-title") }}
      </template>
      <template #content>
        <p>{{ $t("admin.search-sites-description") }}</p>
      </template>
    </BasePageTitle>

    <div class="d-flex justify-end mb-4 gap-2">
      <v-btn
        color="primary"
        @click="addDialog = true"
      >
        {{ $t("admin.search-sites-add") }}
      </v-btn>
      <v-btn
        color="warning"
        variant="outlined"
        @click="confirmRestore"
      >
        {{ $t("admin.search-sites-restore-defaults") }}
      </v-btn>
    </div>

    <v-alert
      v-if="error"
      type="error"
      class="mb-4"
    >
      {{ error }}
    </v-alert>

    <v-data-table
      :headers="headers"
      :items="sites"
      :loading="loading"
    >
      <template #[`item.enabled`]="{ item }">
        <v-switch
          :model-value="item.enabled"
          color="primary"
          hide-details
          density="compact"
          @update:model-value="(val: boolean) => patchSite(item.id, { enabled: val })"
        />
      </template>
      <template #[`item.isBlocked`]="{ item }">
        <v-switch
          :model-value="item.isBlocked"
          color="error"
          hide-details
          density="compact"
          @update:model-value="(val: boolean) => patchSite(item.id, { isBlocked: val })"
        />
      </template>
      <template #[`item.actions`]="{ item }">
        <v-btn
          icon
          variant="text"
          color="error"
          size="small"
          @click="deleteSite(item.id)"
        >
          <v-icon>{{ $globals.icons.delete }}</v-icon>
        </v-btn>
      </template>
    </v-data-table>

    <!-- Add site dialog -->
    <v-dialog
      v-model="addDialog"
      max-width="500"
    >
      <v-card>
        <v-card-title>{{ $t("admin.search-sites-add") }}</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="newSite.name"
            :label="$t('admin.search-sites-name')"
            class="mb-2"
          />
          <v-text-field
            v-model="newSite.domain"
            :label="$t('admin.search-sites-domain')"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="addDialog = false">
            {{ $t("general.cancel") }}
          </v-btn>
          <v-btn
            color="primary"
            :disabled="!newSite.name || !newSite.domain"
            @click="addSite"
          >
            {{ $t("general.save") }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Restore defaults confirm dialog -->
    <v-dialog
      v-model="restoreDialog"
      max-width="500"
    >
      <v-card>
        <v-card-title>{{ $t("admin.search-sites-restore-defaults") }}</v-card-title>
        <v-card-text>{{ $t("admin.search-sites-restore-confirm") }}</v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="restoreDialog = false">
            {{ $t("general.cancel") }}
          </v-btn>
          <v-btn
            color="error"
            @click="restoreDefaults"
          >
            {{ $t("general.confirm") }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { useUserApi } from "~/composables/api";
import type { HouseholdSearchSiteOut } from "~/lib/api/types/household";

definePageMeta({
  middleware: ["group-only"],
});

const { $globals } = useNuxtApp();
const i18n = useI18n();
const api = useUserApi();

useSeoMeta({
  title: i18n.t("admin.search-sites-title"),
});

const sites = ref<HouseholdSearchSiteOut[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const addDialog = ref(false);
const restoreDialog = ref(false);
const newSite = ref({ name: "", domain: "" });

const headers = [
  { title: i18n.t("admin.search-sites-name"), key: "name" },
  { title: i18n.t("admin.search-sites-domain"), key: "domain" },
  { title: i18n.t("admin.search-sites-enabled"), key: "enabled" },
  { title: i18n.t("admin.search-sites-blocked"), key: "isBlocked" },
  { title: "", key: "actions", sortable: false },
];

async function loadSites() {
  loading.value = true;
  try {
    const { data } = await api.households.getSearchSites();
    sites.value = data ?? [];
  }
  catch {
    error.value = i18n.t("generic.server-error");
  }
  finally {
    loading.value = false;
  }
}

async function addSite() {
  const { data } = await api.households.createSearchSite({
    name: newSite.value.name,
    domain: newSite.value.domain,
  });
  if (data) sites.value.push(data);
  newSite.value = { name: "", domain: "" };
  addDialog.value = false;
}

async function patchSite(id: string, patch: { enabled?: boolean; isBlocked?: boolean }) {
  const { data } = await api.households.updateSearchSite(id, patch);
  if (data) {
    const idx = sites.value.findIndex(s => s.id === id);
    if (idx !== -1) sites.value[idx] = data;
  }
}

async function deleteSite(id: string) {
  await api.households.deleteSearchSite(id);
  sites.value = sites.value.filter(s => s.id !== id);
}

function confirmRestore() {
  restoreDialog.value = true;
}

async function restoreDefaults() {
  const { data } = await api.households.restoreDefaultSearchSites();
  if (data) sites.value = data;
  restoreDialog.value = false;
}

onMounted(loadSites);
</script>
