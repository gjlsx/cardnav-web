/**
 * 文件说明: 把中转站结果拆成自然榜与赞助展示，赞助状态不参与自然排序。
 */

export type RankedGatewaySite = {
  name: string;
  siteScore?: number | null;
  modelCount?: number;
  sponsor?: boolean;
};

export type GatewaySiteRanking<T extends RankedGatewaySite = RankedGatewaySite> = {
  natural: T[];
  sponsored: T[];
};

export function compareGatewaySitesNatural(left: RankedGatewaySite, right: RankedGatewaySite) {
  return (right.siteScore ?? 0) - (left.siteScore ?? 0)
    || (right.modelCount ?? 0) - (left.modelCount ?? 0)
    || left.name.localeCompare(right.name, 'zh-Hans-CN');
}

export function splitGatewaySiteRanking<T extends RankedGatewaySite>(sites: readonly T[]): GatewaySiteRanking<T> {
  const natural = sites.slice().sort(compareGatewaySitesNatural);
  return {
    natural,
    sponsored: natural.filter(site => site.sponsor === true),
  };
}

export function paginateGatewayRanking<T extends RankedGatewaySite>(sites: readonly T[], offset: number) {
  const ranking = splitGatewaySiteRanking(sites);
  const safeOffset = Math.max(0, Math.floor(Number(offset) || 0));
  return {
    ...ranking,
    offset: safeOffset,
    items: ranking.natural.slice(safeOffset),
  };
}

export function gatewayOutboundRel(sponsor?: boolean) {
  return sponsor === true ? 'sponsored noopener noreferrer' : 'noopener noreferrer';
}
