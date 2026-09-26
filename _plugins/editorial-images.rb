# frozen_string_literal: true
#
# Gives images in editorial-layout posts what Chirpy's post layout gives its
# own: lazy loading, and real width/height so text doesn't jump as they load
# (and table-of-contents links land in the right place).
#
# Chirpy's `{: w="1200" h="500"}` attributes become width/height; images
# without them get their size from the file (WebP and SVG, which is all
# images/ holds). An image that sets `loading` itself, like the hero, is left
# to load eagerly.

require 'uri'

module EditorialImages
  class << self
    def process(post)
      head, sep, body = post.output.partition(/<article class="post"[^>]*>/)
      return if sep.empty?

      body = body.gsub(/<img\b[^>]*>/) { |tag| rework(tag, post.site.source) }
      post.output = head + sep + body
    end

    private

    def rework(tag, source)
      tag = tag.gsub(/\s(w|h)=(["'])/) { " #{$1 == 'w' ? 'width' : 'height'}=#{$2}" }
      width = tag[/\swidth=["']?(\d+)/, 1]
      height = tag[/\sheight=["']?(\d+)/, 1]
      unless width && height
        size = size_of(tag[/\ssrc="([^"]+)"/, 1], source)
        if size
          # Keep a size the author gave; fill in the other from the file's ratio.
          if width then height = width.to_i * size[1] / size[0]
          elsif height then width = height.to_i * size[0] / size[1]
          else width, height = size
          end
          tag = tag.gsub(/\s(?:width|height)=["']?\d+["']?/, '')
                   .sub(/<img\b/) { %(<img width="#{width}" height="#{height}") }
        end
      end
      tag = tag.sub(/<img\b/, '<img loading="lazy" decoding="async"') unless tag.include?('loading=')
      tag
    end

    def size_of(src, source)
      return unless src&.start_with?('/') && !src.start_with?('//')

      path = File.join(source, URI.decode_uri_component(src.split(/[?#]/).first))
      return unless File.file?(path)

      (@sizes ||= {})[path] ||= File.extname(path).casecmp?('.svg') ? svg_size(path) : webp_size(path)
    end

    # Reads the canvas size from a WebP header (lossy, lossless or extended).
    def webp_size(path)
      data = File.binread(path, 30)
      return unless data&.bytesize == 30 && data[0, 4] == 'RIFF' && data[8, 4] == 'WEBP'

      case data[12, 4]
      when 'VP8 ' then data[26, 4].unpack('v2').map { |n| n & 0x3fff }
      when 'VP8L'
        bits = data[21, 4].unpack1('V')
        [(bits & 0x3fff) + 1, ((bits >> 14) & 0x3fff) + 1]
      when 'VP8X'
        w, h = data[24, 6].unpack('vCvC').each_slice(2).map { |lo, hi| lo + (hi << 16) + 1 }
        [w, h]
      end
    end

    def svg_size(path)
      svg = File.read(path, 2048)
      root = svg[/<svg\b[^>]*>/m] or return
      w = root[/\swidth="([\d.]+)(?:px)?"/, 1]
      h = root[/\sheight="([\d.]+)(?:px)?"/, 1]
      return [w.to_f.round, h.to_f.round] if w && h

      box = root[/viewBox="([^"]+)"/, 1]&.split(/[\s,]+/)&.map(&:to_f)
      [box[2].round, box[3].round] if box&.size == 4
    end
  end
end

Jekyll::Hooks.register :posts, :post_render do |post|
  EditorialImages.process(post) if post.data['layout'] == 'editorial'
end
