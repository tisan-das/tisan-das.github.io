#!/usr/bin/env ruby
#
# Check for changed posts
#
# A post shows "Updated" when a commit after the one that created it changed
# its text. Two kinds of commit don't count:
# - ones that only touch front matter (layout, pin, image, title...), and
# - site-wide maintenance listed in .lastmod-ignore-revs (image format
#   conversions, styling passes), which rewrote every post without updating it.

require 'open3'

IGNORED_REVS = File.readlines(File.join(__dir__, '..', '.lastmod-ignore-revs'), chomp: true)
                   .map { |line| line.sub(/#.*/, '').strip }.reject(&:empty?)

def post_body(rev, path)
  text, = Open3.capture2e('git', 'show', "#{rev}:#{path}")
  text.split(/^---\s*$/, 3)[2]
end

def counts_as_update?(sha, path)
  return false if IGNORED_REVS.any? { |rev| sha.start_with?(rev) }

  post_body(sha, path) != post_body("#{sha}^", path)
end

Jekyll::Hooks.register :posts, :post_init do |post|

  path = post.relative_path
  # Argument arrays, not a shell string, so a filename can't inject commands.
  shas = Open3.capture2('git', 'log', '--format=%H', '--', path)[0].split
  latest = shas[0...-1].find { |sha| counts_as_update?(sha, path) }

  if latest
    lastmod_date, = Open3.capture2('git', 'log', '-1', '--pretty=%ad', '--date=iso', latest)
    post.data['last_modified_at'] = lastmod_date
  end

end
