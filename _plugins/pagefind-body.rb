# frozen_string_literal: true
#
# Marks the body of every Chirpy-layout post for Pagefind.
#
# Once any page carries `data-pagefind-body`, Pagefind indexes only marked
# elements, which keeps tag, category and archive listings out of search
# results. The editorial layout marks its own article; Chirpy's post layout
# lives in the gem, so its `.content` div is tagged here after rendering.

Jekyll::Hooks.register :posts, :post_render do |post|
  next unless post.data['layout'] == 'post'

  post.output = post.output.sub('<div class="content">', '<div class="content" data-pagefind-body>')
end
