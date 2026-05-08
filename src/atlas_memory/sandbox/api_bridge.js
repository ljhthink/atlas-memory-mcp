// API Bridge for Atlas Memory MCP exec_code sandbox.
// Pre-loaded with serialized entity/relation data from Python host.

const _api = __API_CONTEXT__;

const _entities = _api.entities || [];
const _relations = _api.relations || [];
const _observations = _api.observations || [];

const _entityIndex = {};
for (const e of _entities) {
  _entityIndex[e.id] = e;
}

function _match(keyword, items) {
  const k = keyword.toLowerCase();
  return items.filter(
    (e) => e.name.toLowerCase().includes(k) || e.path.toLowerCase().includes(k)
  );
}

const mem = {
  query: function (keyword, opts) {
    opts = opts || {};
    let results = _match(keyword, _entities);
    if (opts.type) {
      results = results.filter((e) => e.type === opts.type);
    }
    const limit = opts.limit || 20;
    const offset = opts.offset || 0;
    return results.slice(offset, offset + limit);
  },

  get: function (entityId) {
    return _entityIndex[entityId] || null;
  },

  semantic: function (_query, _topK) {
    return [];
  },

  relations: function (entityId, direction) {
    direction = direction || "both";
    let rels;
    if (direction === "out") {
      rels = _relations.filter((r) => r.from_id === entityId);
    } else if (direction === "in") {
      rels = _relations.filter((r) => r.to_id === entityId);
    } else {
      rels = _relations.filter((r) => r.from_id === entityId || r.to_id === entityId);
    }
    return rels.map((r) => ({
      ...r,
      from_name: (_entityIndex[r.from_id] || {}).name || r.from_id,
      to_name: (_entityIndex[r.to_id] || {}).name || r.to_id,
    }));
  },

  observations: function (entityId, limit, offset) {
    const obs = _observations
      .filter((o) => o.entity_id === entityId)
      .sort((a, b) => b.created_at - a.created_at);
    return obs.slice(offset || 0, (offset || 0) + (limit || 10));
  },

  observe: function (_entityId, _content) {
    return { __op: 'observe', entity_id: _entityId, content: _content };
  },
};

// ---- USER CODE BELOW ----
// __USER_CODE__
