import { BaseCRUDAPIReadOnly } from "../base/base-clients";
import type { PaginationData } from "../types/non-generated";
import type { QueryValue } from "../base/route";
import type { UserOut } from "~/lib/api/types/user";
import type {
  HouseholdInDB,
  HouseholdStatistics,
  ReadHouseholdPreferences,
  SetPermissions,
  UpdateHouseholdPreferences,
  CreateInviteToken,
  ReadInviteToken,
  HouseholdSummary,
  HouseholdRecipeSummary,
  HouseholdSearchSiteCreate,
  HouseholdSearchSiteOut,
  HouseholdSearchSiteUpdate,
  HuntSearchRequest,
  HuntSearchResponse,
} from "~/lib/api/types/household";

const prefix = "/api";

const routes = {
  households: `${prefix}/groups/households`,
  householdsSelf: `${prefix}/households/self`,
  members: `${prefix}/households/members`,
  permissions: `${prefix}/households/permissions`,

  preferences: `${prefix}/households/preferences`,
  statistics: `${prefix}/households/statistics`,
  invitation: `${prefix}/households/invitations`,

  searchSites: `${prefix}/households/search-sites`,
  searchSitesId: (id: string) => `${prefix}/households/search-sites/${id}`,
  searchSitesRestoreDefaults: `${prefix}/households/search-sites/restore-defaults`,
  huntSearch: `${prefix}/recipes/hunt/search`,

  householdsId: (id: string | number) => `${prefix}/groups/households/${id}`,
  householdsSelfRecipesSlug: (recipeSlug: string) => `${prefix}/households/self/recipes/${recipeSlug}`,
};

export class HouseholdAPI extends BaseCRUDAPIReadOnly<HouseholdSummary> {
  baseRoute = routes.households;
  itemRoute = routes.householdsId;
  /** Returns the Household Data for the Current User
   */
  async getCurrentUserHousehold() {
    return await this.requests.get<HouseholdInDB>(routes.householdsSelf);
  }

  async getCurrentUserHouseholdRecipe(recipeSlug: string) {
    return await this.requests.get<HouseholdRecipeSummary>(routes.householdsSelfRecipesSlug(recipeSlug));
  }

  async setPreferences(payload: UpdateHouseholdPreferences) {
    // TODO: This should probably be a patch request, which isn't offered by the API currently
    return await this.requests.put<ReadHouseholdPreferences, UpdateHouseholdPreferences>(routes.preferences, payload);
  }

  async createInvitation(payload: CreateInviteToken) {
    return await this.requests.post<ReadInviteToken>(routes.invitation, payload);
  }

  async fetchMembers(page = 1, perPage = -1, params = {} as Record<string, QueryValue>) {
    return await this.requests.get<PaginationData<UserOut>>(routes.members, { page, perPage, ...params });
  }

  async setMemberPermissions(payload: SetPermissions) {
    // TODO: This should probably be a patch request, which isn't offered by the API currently
    return await this.requests.put<UserOut, SetPermissions>(routes.permissions, payload);
  }

  async statistics() {
    return await this.requests.get<HouseholdStatistics>(routes.statistics);
  }

  async getSearchSites() {
    return await this.requests.get<HouseholdSearchSiteOut[]>(routes.searchSites);
  }

  async createSearchSite(payload: HouseholdSearchSiteCreate) {
    return await this.requests.post<HouseholdSearchSiteOut>(routes.searchSites, payload);
  }

  async updateSearchSite(id: string, payload: HouseholdSearchSiteUpdate) {
    return await this.requests.put<HouseholdSearchSiteOut, HouseholdSearchSiteUpdate>(routes.searchSitesId(id), payload);
  }

  async deleteSearchSite(id: string) {
    return await this.requests.delete(routes.searchSitesId(id));
  }

  async restoreDefaultSearchSites() {
    return await this.requests.post<HouseholdSearchSiteOut[]>(routes.searchSitesRestoreDefaults, {});
  }

  async huntSearch(payload: HuntSearchRequest) {
    return await this.requests.post<HuntSearchResponse>(routes.huntSearch, payload);
  }
}
