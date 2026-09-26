# frozen_string_literal: true
#
# Fills in the script hashes of the Content Security Policy <meta> tag in
# editorial-head.html. The policy is a <meta> tag because GitHub Pages can't
# send headers.
#
# Inline scripts are allowed by their SHA-256 hash, taken from the finished
# page, so the site's own scripts run and any other injected script doesn't.
# The HTML parser turns CRLF into LF before the browser hashes a script, so
# the hash is taken the same way; a Windows build then matches Linux.

require 'base64'
require 'digest'

module ContentSecurityPolicy
  TOKEN = '{SCRIPT_HASHES}'
  # Inline scripts, minus JSON-LD data blocks, which never run.
  INLINE_SCRIPT = %r{<script(?![^>]*\bsrc=)(?![^>]*application/ld\+json)[^>]*>(.*?)</script>}m

  def self.apply(doc)
    return unless doc.output&.include?(TOKEN)

    hashes = doc.output.scan(INLINE_SCRIPT).flatten.uniq.map do |js|
      "'sha256-#{Base64.strict_encode64(Digest::SHA256.digest(js.gsub(/\r\n?/, "\n")))}'"
    end
    doc.output = doc.output.sub(TOKEN, hashes.join(' '))
  end
end

# Low priority: runs after the other post_render hooks have finished the page.
Jekyll::Hooks.register [:pages, :documents], :post_render, priority: :low do |doc|
  ContentSecurityPolicy.apply(doc)
end
