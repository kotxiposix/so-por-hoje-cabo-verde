import assert from "node:assert/strict";
import test from "node:test";

import {
  normalizePublishedCommunityPost,
  normalizePublishedCommunityPosts,
} from "../public/community-posts.mjs";

const validPost = {
  id: "7a0c9820-4e7a-40f6-a32b-6f5ce402ef68",
  pseudonym: "Guerreiro1234",
  body: "  Um dia\n de cada vez. ",
  created_at: "2026-09-27T12:00:00Z",
};

test("normalizes the minimal public community contract", () => {
  assert.deepEqual(normalizePublishedCommunityPost(validPost), {
    id: validPost.id,
    pseudonym: "Guerreiro1234",
    body: "Um dia de cada vez.",
    created_at: "2026-09-27T12:00:00.000Z",
  });
});

test("rejects malformed identifiers, pseudonyms, bodies and dates", () => {
  assert.equal(normalizePublishedCommunityPost({ ...validPost, id: "post-one" }), null);
  assert.equal(normalizePublishedCommunityPost({ ...validPost, pseudonym: "Nome real" }), null);
  assert.equal(normalizePublishedCommunityPost({ ...validPost, body: "a".repeat(281) }), null);
  assert.equal(normalizePublishedCommunityPost({ ...validPost, created_at: "ontem" }), null);
  assert.equal(normalizePublishedCommunityPost({ ...validPost, created_at: "2026-09-27" }), null);
});

test("filters duplicates and respects the public result limit", () => {
  const second = {
    ...validPost,
    id: "93ebd2df-cfa5-4a28-8b43-5b687ea88212",
    pseudonym: "Guerreiro9876",
  };
  const result = normalizePublishedCommunityPosts([
    validPost,
    { ...validPost },
    { ...validPost, id: "invalid" },
    second,
  ], 2);

  assert.deepEqual(result.map((post) => post.id), [validPost.id, second.id]);
});
