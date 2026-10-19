using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using ProductApi.Data;
using ProductApi.Models;

namespace ProductApi.Controllers;

[ApiController]
[Route("api/[controller]")]
public class ProductsController : ControllerBase
{
    private readonly MyDatabaseContext _context;

    public ProductsController(MyDatabaseContext context)
    {
        _context = context;
    }

    [HttpGet]
    public async Task<ActionResult<List<StoreProduct>>> GetProducts([FromQuery] string? search)
    {
        var query = _context.StoreProducts.AsNoTracking();
        if (!string.IsNullOrWhiteSpace(search))
        {
            var term = search.Trim().ToLower();
            query = query.Where(p => p.Name.ToLower().Contains(term)
                || p.Description.ToLower().Contains(term)
                || p.Category.ToLower().Contains(term));
        }
        return await query.OrderByDescending(p => p.CreatedAt).ThenBy(p => p.Id).ToListAsync();
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<StoreProduct>> GetProduct(string id)
    {
        var product = await _context.StoreProducts.FindAsync(id);
        if (product == null) return NotFound();
        return Ok(product);
    }

    [HttpPost]
    public async Task<ActionResult<StoreProduct>> CreateProduct(StoreProduct product)
    {
        // New catalog entries get server-generated IDs; imports keep their original IDs.
        product.Id = Guid.NewGuid().ToString("N");
        product.CreatedAt = product.UpdatedAt = DateTime.UtcNow;
        _context.StoreProducts.Add(product);
        await _context.SaveChangesAsync();
        return CreatedAtAction(nameof(GetProduct), new { id = product.Id }, product);
    }

    [HttpPut("{id}")]
    public async Task<IActionResult> UpdateProduct(string id, StoreProduct updatedProduct)
    {
        var product = await _context.StoreProducts.FindAsync(id);
        if (product == null) return NotFound();

        product.Name = updatedProduct.Name;
        product.Description = updatedProduct.Description;
        product.Price = updatedProduct.Price;
        product.Stock = updatedProduct.Stock;
        product.ImageUrl = updatedProduct.ImageUrl;
        product.Category = updatedProduct.Category;
        product.UpdatedAt = DateTime.UtcNow;
        await _context.SaveChangesAsync();
        return Ok(product);
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> DeleteProduct(string id)
    {
        var product = await _context.StoreProducts.FindAsync(id);
        if (product == null) return NotFound();
        _context.StoreProducts.Remove(product);
        await _context.SaveChangesAsync();
        return NoContent();
    }
}
