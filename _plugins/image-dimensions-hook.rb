# frozen_string_literal: true
#
# Adds width/height to markdown images automatically, at build time.
#
# Why: Chirpy emits images with `loading="lazy"` and no intrinsic size, so the
# browser reserves zero height until the file arrives and the surrounding text
# jumps. Chirpy's own fix is to write kramdown attributes by hand:
#
#     ![alt](/images/foo.webp){: w="1200" h="690" }
#
# That is opaque to read and easy to get wrong, so this hook reads the real
# dimensions from the file instead and a post only needs:
#
#     ![alt](/images/foo.webp)
#
# Existing `{: ... }` annotations are left alone (the negative lookahead), so it
# is safe to adopt gradually. The editorial layout reuses `read` for images the
# hook can't reach (_plugins/editorial-content.rb).

require 'uri'

module ImageDimensions
  module_function

  # Returns [width, height] for PNG, WebP or SVG, or nil if it cannot tell.
  def read(path)
    return nil unless File.file?(path)
    return read_svg(path) if File.extname(path).casecmp?('.svg')

    head = File.binread(path, 64)
    return nil if head.nil? || head.bytesize < 30

    if head[0, 8] == "\x89PNG\r\n\x1a\n".b # IHDR width/height are big-endian at 16..24
      head[16, 8].unpack('NN')
    elsif head[0, 4] == 'RIFF' && head[8, 4] == 'WEBP'
      read_webp(head)
    end
  rescue StandardError
    nil
  end

  def read_webp(head)
    case head[12, 4]
    when 'VP8 ' # lossy: frame tag (3) + start code (3), then 14-bit w and h
      [head[26, 2].unpack1('v') & 0x3FFF, head[28, 2].unpack1('v') & 0x3FFF]
    when 'VP8L' # lossless: 14-bit (w-1) and (h-1) packed into one word
      bits = head[21, 4].unpack1('V')
      [(bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1]
    when 'VP8X' # extended: 24-bit little-endian canvas (w-1) and (h-1)
      head[24, 6].unpack('vCvC').each_slice(2).map { |lo, hi| lo + (hi << 16) + 1 }
    end
  end

  # width/height attributes when present, else the viewBox size.
  def read_svg(path)
    root = File.read(path, 2048)[/<svg\b[^>]*>/m] or return nil
    w = root[/\swidth="([\d.]+)(?:px)?"/, 1]
    h = root[/\sheight="([\d.]+)(?:px)?"/, 1]
    return [w.to_f.round, h.to_f.round] if w && h

    box = root[/viewBox="([^"]+)"/, 1]&.split(/[\s,]+/)&.map(&:to_f)
    [box[2].round, box[3].round] if box&.size == 4
  end
end

Jekyll::Hooks.register :posts, :pre_render do |post|
  post.content = post.content.gsub(%r{^(!\[[^\]]*\]\((/[^)\s]+)\))(?!\s*\{:)}) do
    tag = Regexp.last_match(1)
    src = Regexp.last_match(2)
    dims = ImageDimensions.read(File.join(post.site.source, URI.decode_uri_component(src)))
    dims ? %(#{tag}{: w="#{dims[0]}" h="#{dims[1]}" }) : tag
  end
end
