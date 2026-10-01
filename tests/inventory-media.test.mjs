import test from 'node:test';
import assert from 'node:assert/strict';
import {imageUrls} from '../src/crm-logic.mjs';
test('Sheet Cloudinary photos are used for property cards',()=>{
 const row={cloudinary_image_urls:['https://res.cloudinary.com/dcvwsclyc/image/upload/v1/photo_1.jpg','https://res.cloudinary.com/dcvwsclyc/image/upload/v1/photo_2.jpg']};
 assert.equal(imageUrls(row).length,2);
 assert.deepEqual(imageUrls({cloudinary_image_urls:[]}),[]);
 assert.deepEqual(imageUrls({photos:['https://example.com/authorized.jpg']}),['https://example.com/authorized.jpg']);
 assert.deepEqual(imageUrls({cloudinary_image_urls:'https://res.cloudinary.com/a.jpg, https://res.cloudinary.com/b.jpg'}),['https://res.cloudinary.com/a.jpg','https://res.cloudinary.com/b.jpg']);
 assert.deepEqual(imageUrls({cloudinary_image_urls:'["https://res.cloudinary.com/c.jpg",{"secure_url":"https://res.cloudinary.com/d.jpg"}]'}),['https://res.cloudinary.com/c.jpg','https://res.cloudinary.com/d.jpg']);
 assert.deepEqual(imageUrls({cloudinary_image_urls:[{"secure_url":"https://res.cloudinary.com/e.jpg"},"not-a-url"]}),['https://res.cloudinary.com/e.jpg']);
});
